# Databricks Notebook: 08_Kafka_ICU_Vitals_Stream_NB.py
# MediFlow360 — Spark Structured Streaming: ICU Vitals from Kafka → Bronze Delta
# Author: Kavitha Rajan (DE-003) | Reviewed: Priya Sharma (DE-001)
# Version: 1.0 | Last Updated: 2024-04-05
# Trigger: Continuous / ProcessingTime("30 seconds") via Airflow dag_kafka_stream_monitor.py

# ─────────────────────────────────────────────────────────────────────────────
# PREREQUISITES (cluster-level libs — install via cluster policy or init script):
#   org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1
#   io.delta:delta-core_2.12:2.4.0
# ─────────────────────────────────────────────────────────────────────────────

%run ./00_Helper_NB

from pyspark.sql.functions import (
    col, lit, from_json, current_timestamp, window,
    to_timestamp, when, expr, struct, avg, max as spark_max,
    count, sum as spark_sum, percentile_approx
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, TimestampType, LongType
)
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: PARAMETERS & CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

# Widget parameters (set by Airflow DAG via Databricks Jobs API)
STREAMING_MODE = dbutils.widgets.get("streaming_mode") \
    if "streaming_mode" in [w.name for w in dbutils.widgets.getAll()] \
    else "continuous"  # "continuous" | "batch" (trigger once)

TRIGGER_INTERVAL = dbutils.widgets.get("trigger_interval") \
    if "trigger_interval" in [w.name for w in dbutils.widgets.getAll()] \
    else "30 seconds"

RUN_ID = f"kafka-vitals-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

# ─── Kafka / Event Hubs config ─────────────────────────────────────────────
KAFKA_BOOTSTRAP  = get_secret("kafka-bootstrap-servers")          # Event Hubs: <ns>.servicebus.windows.net:9093
KAFKA_TOPIC      = "mrhs.icu.vitals"
CONSUMER_GROUP   = "mediflow360-vitals-consumer-grp"

KAFKA_OPTIONS = {
    "kafka.bootstrap.servers":           KAFKA_BOOTSTRAP,
    "kafka.security.protocol":           "SASL_SSL",
    "kafka.sasl.mechanism":              "PLAIN",
    "kafka.sasl.jaas.config":            (
        f"kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required "
        f"username=\"$ConnectionString\" "
        f"password=\"{get_secret('event-hub-connection-string')}\";"
    ),
    "subscribe":                         KAFKA_TOPIC,
    "startingOffsets":                   "latest",   # Use "earliest" for full replay
    "failOnDataLoss":                    "false",
    "maxOffsetsPerTrigger":              "5000",      # Backpressure control
    "kafka.group.id":                    CONSUMER_GROUP,
}

# ─── Checkpoint & output paths ─────────────────────────────────────────────
CHECKPOINT_PATH  = f"{ABFSS_PATH}/streaming/checkpoints/vitals"
BRONZE_TABLE     = f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.icu_vitals_stream"
DLQ_TABLE        = f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.icu_vitals_dlq"  # Dead Letter Queue

print(f"[Vitals Stream] Run ID: {RUN_ID}")
print(f"[Vitals Stream] Mode: {STREAMING_MODE} | Trigger: {TRIGGER_INTERVAL}")
print(f"[Vitals Stream] Topic: {KAFKA_TOPIC} | Checkpoint: {CHECKPOINT_PATH}")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: AVRO/JSON SCHEMA DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

VITALS_SCHEMA = StructType([
    StructField("event_type",           StringType(),  True),
    StructField("schema_version",       StringType(),  True),
    StructField("device_id",            StringType(),  True),
    StructField("patient_mrn",          StringType(),  True),
    StructField("hospital_code",        StringType(),  True),
    StructField("bed_number",           IntegerType(), True),
    StructField("heart_rate",           IntegerType(), True),
    StructField("spo2",                 DoubleType(),  True),
    StructField("systolic_bp",          IntegerType(), True),
    StructField("diastolic_bp",         IntegerType(), True),
    StructField("temperature_c",        DoubleType(),  True),
    StructField("respiratory_rate",     IntegerType(), True),
    StructField("is_anomaly_injected",  BooleanType(), True),
    StructField("recorded_at",          StringType(),  True),
    StructField("ingestion_source",     StringType(),  True),
])

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: STREAMING INGESTION
# ═══════════════════════════════════════════════════════════════════════════════

def create_vitals_stream():
    """
    Create Spark Structured Streaming DataFrame from Kafka.
    Returns parsed vitals DataFrame with event timestamp as watermark anchor.
    """
    raw_stream = (
        spark.readStream
             .format("kafka")
             .options(**KAFKA_OPTIONS)
             .load()
    )

    # Parse JSON payload
    parsed = (
        raw_stream
        .select(
            col("key").cast("string").alias("kafka_key"),
            from_json(col("value").cast("string"), VITALS_SCHEMA).alias("data"),
            col("topic"),
            col("partition"),
            col("offset"),
            col("timestamp").alias("kafka_timestamp"),
        )
        .select(
            col("kafka_key"),
            col("data.*"),
            col("topic"),
            col("partition"),
            col("offset"),
            col("kafka_timestamp"),
        )
    )

    # Parse recorded_at and apply 5-minute watermark for late data handling
    enriched = (
        parsed
        .withColumn("event_ts",  to_timestamp(col("recorded_at")))
        .withWatermark("event_ts", "5 minutes")
        .withColumn("_source_system",    lit("KAFKA_ICU_VITALS"))
        .withColumn("_load_timestamp",   current_timestamp())
        .withColumn("_run_id",           lit(RUN_ID))
        .withColumn("_kafka_partition",  col("partition"))
        .withColumn("_kafka_offset",     col("offset"))
        # Clinical severity classification
        .withColumn("alert_level",
            when(
                (col("heart_rate") < 45) | (col("heart_rate") > 130) |
                (col("spo2") < 90.0) | (col("systolic_bp") > 180) |
                (col("temperature_c") > 39.5),
                "CRITICAL"
            ).when(
                (col("heart_rate") < 55) | (col("heart_rate") > 110) |
                (col("spo2") < 94.0) | (col("systolic_bp") > 160),
                "WARNING"
            ).otherwise("NORMAL")
        )
        # Data quality flag
        .withColumn("dq_passed",
            (col("heart_rate").between(20, 300)) &
            (col("spo2").between(70.0, 100.0)) &
            (col("systolic_bp").between(50, 250)) &
            col("patient_mrn").isNotNull() &
            col("device_id").isNotNull()
        )
    )

    return enriched


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: MICRO-BATCH PROCESSOR (foreachBatch)
# ═══════════════════════════════════════════════════════════════════════════════

def process_vitals_batch(batch_df, batch_id: int):
    """
    Process each micro-batch:
    1. Route DQ-failed records to Dead Letter Queue (DLQ)
    2. Write valid records to Bronze Delta table
    3. Write streaming audit log
    4. Send CRITICAL alerts via Teams webhook
    """
    if batch_df.isEmpty():
        print(f"[Vitals Stream] Batch {batch_id}: Empty micro-batch. Skipping.")
        return

    batch_start = datetime.now(timezone.utc)
    total_count = batch_df.count()

    # ── Route: valid vs. DLQ ──────────────────────────────────────────────────
    valid_df = batch_df.filter(col("dq_passed") == True)
    dlq_df   = batch_df.filter(col("dq_passed") == False) \
                        .withColumn("rejection_reason", lit("DQ validation failed: out-of-range vital signs"))

    valid_count   = valid_df.count()
    invalid_count = dlq_df.count()

    print(f"[Vitals Stream] Batch {batch_id}: Total={total_count} | Valid={valid_count} | DLQ={invalid_count}")

    # ── Write valid records → Bronze Delta ────────────────────────────────────
    if valid_count > 0:
        (
            valid_df
            .drop("dq_passed")
            .write
            .format("delta")
            .option("mergeSchema", "true")
            .mode("append")
            .saveAsTable(BRONZE_TABLE)
        )
        print(f"[Vitals Stream] ✅ Written {valid_count} records → {BRONZE_TABLE}")

    # ── Write DLQ records ────────────────────────────────────────────────────
    if invalid_count > 0:
        (
            dlq_df
            .write
            .format("delta")
            .option("mergeSchema", "true")
            .mode("append")
            .saveAsTable(DLQ_TABLE)
        )
        print(f"[Vitals Stream] ⚠️  {invalid_count} records → DLQ: {DLQ_TABLE}")

    # ── Send CRITICAL patient alerts via Teams ────────────────────────────────
    critical_df = valid_df.filter(col("alert_level") == "CRITICAL")
    critical_count = critical_df.count()
    if critical_count > 0:
        critical_rows = critical_df.select(
            "device_id", "patient_mrn", "hospital_code",
            "heart_rate", "spo2", "systolic_bp", "temperature_c", "alert_level"
        ).limit(5).collect()

        critical_summary = "; ".join([
            f"{r['device_id']} (HR:{r['heart_rate']}, SpO2:{r['spo2']}, SysBP:{r['systolic_bp']}, Temp:{r['temperature_c']})"
            for r in critical_rows
        ])
        send_alert(
            severity=SEVERITY_CRITICAL,
            title=f"🚨 ICU Critical Vitals — {critical_count} patients",
            message=f"Batch {batch_id}: {critical_summary}",
            pipeline="08_Kafka_ICU_Vitals_Stream_NB",
            entity="icu_vitals_stream",
        )

    # ── Streaming audit log ───────────────────────────────────────────────────
    batch_end = datetime.now(timezone.utc)
    write_audit_log(
        pipeline_name="PL_Kafka_Vitals_Stream",
        notebook_name="08_Kafka_ICU_Vitals_Stream_NB",
        run_id=f"{RUN_ID}-b{batch_id}",
        source_system="KAFKA_ICU_VITALS",
        entity_name="icu_vitals_stream",
        records_read=total_count,
        records_written=valid_count,
        records_rejected=invalid_count,
        status="SUCCESS",
        start_time=batch_start,
        end_time=batch_end,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: LAUNCH STREAMING QUERY
# ═══════════════════════════════════════════════════════════════════════════════

vitals_stream = create_vitals_stream()

if STREAMING_MODE == "continuous":
    # Continuous micro-batch (for production)
    query = (
        vitals_stream
        .writeStream
        .foreachBatch(process_vitals_batch)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(processingTime=TRIGGER_INTERVAL)
        .queryName("mediflow360_vitals_stream")
        .start()
    )
    print(f"[Vitals Stream] 🚀 Continuous stream started. Query ID: {query.id}")
    query.awaitTermination()

elif STREAMING_MODE == "batch":
    # Trigger once — used for Airflow backfill DAG runs
    query = (
        vitals_stream
        .writeStream
        .foreachBatch(process_vitals_batch)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(once=True)
        .queryName("mediflow360_vitals_batch_trigger")
        .start()
    )
    query.awaitTermination()
    print(f"[Vitals Stream] ✅ Batch trigger complete. Query: {query.id}")

print("[Vitals Stream] Streaming job terminated cleanly.")
