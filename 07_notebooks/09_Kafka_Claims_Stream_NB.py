# Databricks Notebook: 09_Kafka_Claims_Stream_NB.py
# MediFlow360 — Spark Structured Streaming: Claims from Kafka → Bronze Delta
# Author: Arjun Patel (DE-002)
# Version: 1.0 | Last Updated: 2024-04-06
# Trigger: ProcessingTime("2 minutes") via Airflow dag_bronze_batch_ingestion.py

%run ./00_Helper_NB

from pyspark.sql.functions import (
    col, lit, from_json, current_timestamp, to_timestamp,
    to_date, when, arrays_to_string, expr, size, array_contains
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    BooleanType, ArrayType, TimestampType
)
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════════
# PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

RUN_ID           = f"kafka-claims-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
STREAMING_MODE   = dbutils.widgets.get("streaming_mode") \
    if "streaming_mode" in [w.name for w in dbutils.widgets.getAll()] else "continuous"
TRIGGER_INTERVAL = dbutils.widgets.get("trigger_interval") \
    if "trigger_interval" in [w.name for w in dbutils.widgets.getAll()] else "2 minutes"

KAFKA_TOPIC    = "mrhs.insurance.claims"
CONSUMER_GROUP = "mediflow360-claims-consumer-grp"

KAFKA_OPTIONS = {
    "kafka.bootstrap.servers": get_secret("kafka-bootstrap-servers"),
    "kafka.security.protocol": "SASL_SSL",
    "kafka.sasl.mechanism":    "PLAIN",
    "kafka.sasl.jaas.config": (
        f"kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required "
        f"username=\"$ConnectionString\" "
        f"password=\"{get_secret('event-hub-connection-string')}\";"
    ),
    "subscribe":               KAFKA_TOPIC,
    "startingOffsets":         "latest",
    "failOnDataLoss":          "false",
    "maxOffsetsPerTrigger":    "2000",
    "kafka.group.id":          CONSUMER_GROUP,
}

CHECKPOINT_PATH = f"{ABFSS_PATH}/streaming/checkpoints/claims"
BRONZE_TABLE    = f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.claims_stream"
DLQ_TABLE       = f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.claims_dlq"

print(f"[Claims Stream] Run ID: {RUN_ID} | Mode: {STREAMING_MODE}")

# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

CLAIMS_SCHEMA = StructType([
    StructField("event_type",       StringType(),            True),
    StructField("schema_version",   StringType(),            True),
    StructField("claim_id",         StringType(),            False),
    StructField("patient_mrn",      StringType(),            True),
    StructField("hospital_code",    StringType(),            True),
    StructField("insurer_code",     StringType(),            True),
    StructField("claim_amount",     DoubleType(),            True),
    StructField("approved_amount",  DoubleType(),            True),
    StructField("status",           StringType(),            True),
    StructField("service_date",     StringType(),            True),
    StructField("submitted_at",     StringType(),            True),
    StructField("processed_at",     StringType(),            True),
    StructField("icd_codes",        ArrayType(StringType()), True),
    StructField("procedure_codes",  ArrayType(StringType()), True),
    StructField("is_inpatient",     BooleanType(),           True),
    StructField("ingestion_source", StringType(),            True),
])

# ═══════════════════════════════════════════════════════════════════════════════
# STREAM CREATION
# ═══════════════════════════════════════════════════════════════════════════════

def create_claims_stream():
    """Create claims Structured Streaming DataFrame with schema validation."""
    raw = (
        spark.readStream
             .format("kafka")
             .options(**KAFKA_OPTIONS)
             .load()
    )

    parsed = (
        raw.select(
            col("key").cast("string").alias("kafka_key"),
            from_json(col("value").cast("string"), CLAIMS_SCHEMA).alias("data"),
            col("offset"),
            col("partition"),
            col("timestamp").alias("kafka_ts"),
        )
        .select("kafka_key", "data.*", "offset", "partition", "kafka_ts")
    )

    enriched = (
        parsed
        .withColumn("submitted_ts",       to_timestamp(col("submitted_at")))
        .withWatermark("submitted_ts",    "30 minutes")   # Claims API can be 30min behind
        .withColumn("service_date_ts",    to_date(col("service_date")))
        .withColumn("icd_codes_str",      arrays_to_string(col("icd_codes"), "|"))
        .withColumn("procedure_codes_str",arrays_to_string(col("procedure_codes"), "|"))
        .withColumn("icd_count",          size(col("icd_codes")))
        # Business rule: flag high-value claims (> ₹1,00,000) for manual review
        .withColumn("is_high_value",      col("claim_amount") > 100000.0)
        # Approval ratio (null-safe)
        .withColumn("approval_ratio",
            when(col("claim_amount") > 0,
                 col("approved_amount") / col("claim_amount")
            ).otherwise(None)
        )
        # Fraud risk indicator: denied + high value = elevated scrutiny
        .withColumn("fraud_risk_flag",
            (col("status") == "DENIED") & (col("claim_amount") > 50000.0)
        )
        # Metadata
        .withColumn("_source_system",  lit("KAFKA_CLAIMS"))
        .withColumn("_load_timestamp", current_timestamp())
        .withColumn("_run_id",         lit(RUN_ID))
        .withColumn("_kafka_offset",   col("offset"))
        # DQ validation
        .withColumn("dq_passed",
            col("claim_id").isNotNull() &
            col("patient_mrn").isNotNull() &
            col("claim_amount").isNotNull() &
            (col("claim_amount") > 0) &
            col("status").isin("PENDING", "APPROVED", "DENIED", "PARTIAL") &
            col("hospital_code").isin("CHN", "MDU", "CBE", "TRV")
        )
    )

    return enriched


# ═══════════════════════════════════════════════════════════════════════════════
# MICRO-BATCH PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════

def process_claims_batch(batch_df, batch_id: int):
    """
    Process each micro-batch:
    1. Separate valid vs. DLQ records
    2. Write valid claims to Bronze Delta
    3. Check for fraud risk and high-value claims — alert if threshold exceeded
    4. Write audit log
    """
    if batch_df.isEmpty():
        print(f"[Claims Stream] Batch {batch_id}: Empty. Skipping.")
        return

    batch_start   = datetime.now(timezone.utc)
    total_count   = batch_df.count()

    valid_df      = batch_df.filter(col("dq_passed") == True)
    dlq_df        = batch_df.filter(col("dq_passed") == False) \
                            .withColumn("rejection_reason", lit("Claims DQ: invalid claim_id, amount, status, or hospital_code"))

    valid_count   = valid_df.count()
    invalid_count = dlq_df.count()

    print(f"[Claims Stream] Batch {batch_id}: Total={total_count} | Valid={valid_count} | DLQ={invalid_count}")

    # Write to Bronze
    if valid_count > 0:
        (
            valid_df
            .drop("dq_passed", "icd_codes", "procedure_codes")   # Store as string, not array (JDBC compat)
            .write
            .format("delta")
            .option("mergeSchema", "true")
            .mode("append")
            .saveAsTable(BRONZE_TABLE)
        )
        print(f"[Claims Stream] ✅ {valid_count} claims → {BRONZE_TABLE}")

    if invalid_count > 0:
        (
            dlq_df.write.format("delta")
            .option("mergeSchema", "true")
            .mode("append")
            .saveAsTable(DLQ_TABLE)
        )
        print(f"[Claims Stream] ⚠️  {invalid_count} claims → DLQ")

    # Fraud risk alert
    fraud_count   = valid_df.filter(col("fraud_risk_flag") == True).count() if valid_count > 0 else 0
    highval_count = valid_df.filter(col("is_high_value") == True).count() if valid_count > 0 else 0

    if fraud_count > 0:
        send_alert(
            severity=SEVERITY_WARNING,
            title=f"🔍 Fraud Risk Claims Detected — {fraud_count} claims",
            message=f"Batch {batch_id}: {fraud_count} denied high-value claims flagged for review. High-value total: {highval_count}",
            pipeline="09_Kafka_Claims_Stream_NB",
            entity="claims_stream",
        )

    batch_end = datetime.now(timezone.utc)
    write_audit_log(
        pipeline_name="PL_Kafka_Claims_Stream",
        notebook_name="09_Kafka_Claims_Stream_NB",
        run_id=f"{RUN_ID}-b{batch_id}",
        source_system="KAFKA_CLAIMS",
        entity_name="claims_stream",
        records_read=total_count,
        records_written=valid_count,
        records_rejected=invalid_count,
        status="SUCCESS",
        start_time=batch_start,
        end_time=batch_end,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAUNCH
# ═══════════════════════════════════════════════════════════════════════════════

claims_stream = create_claims_stream()

if STREAMING_MODE == "continuous":
    query = (
        claims_stream
        .writeStream
        .foreachBatch(process_claims_batch)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(processingTime=TRIGGER_INTERVAL)
        .queryName("mediflow360_claims_stream")
        .start()
    )
    print(f"[Claims Stream] 🚀 Stream running. Query ID: {query.id}")
    query.awaitTermination()
else:
    query = (
        claims_stream
        .writeStream
        .foreachBatch(process_claims_batch)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(once=True)
        .queryName("mediflow360_claims_batch")
        .start()
    )
    query.awaitTermination()
    print(f"[Claims Stream] ✅ Batch trigger complete.")
