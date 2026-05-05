# Databricks Notebook: 10_Kafka_Pharmacy_CDC_Stream_NB.py
# MediFlow360 — Spark Structured Streaming: Pharmacy CDC (Debezium) → Bronze Delta MERGE
# Author: Kavitha Rajan (DE-003)
# Version: 1.0 | Last Updated: 2024-04-07
# Trigger: ProcessingTime("1 minute") — CDC requires near-real-time MERGE

%run ./00_Helper_NB

from pyspark.sql.functions import (
    col, lit, from_json, current_timestamp, to_timestamp,
    when, get_json_object, udf
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, LongType, MapType
)
from delta.tables import DeltaTable
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════════════════════
# PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

RUN_ID           = f"kafka-cdc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
STREAMING_MODE   = dbutils.widgets.get("streaming_mode") \
    if "streaming_mode" in [w.name for w in dbutils.widgets.getAll()] else "continuous"
TRIGGER_INTERVAL = "1 minute"

KAFKA_TOPIC    = "mrhs.pharmacy.cdc"
CONSUMER_GROUP = "mediflow360-pharmacy-cdc-grp"

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
    "maxOffsetsPerTrigger":    "1000",
    "kafka.group.id":          CONSUMER_GROUP,
}

CHECKPOINT_PATH  = f"{ABFSS_PATH}/streaming/checkpoints/pharmacy_cdc"
INVENTORY_TABLE  = f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.pharmacy_inventory_stream"
DISPENSE_TABLE   = f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.pharmacy_dispensing_stream"

print(f"[Pharmacy CDC] Run ID: {RUN_ID}")

# ═══════════════════════════════════════════════════════════════════════════════
# CDC ENVELOPE SCHEMA (Debezium format)
# ═══════════════════════════════════════════════════════════════════════════════

# Inventory row schema
INVENTORY_SCHEMA = StructType([
    StructField("inventory_id",   StringType(),  True),
    StructField("ndc_code",       StringType(),  True),
    StructField("drug_name",      StringType(),  True),
    StructField("drug_category",  StringType(),  True),
    StructField("hospital_code",  StringType(),  True),
    StructField("quantity_units", IntegerType(), True),
    StructField("reorder_level",  IntegerType(), True),
    StructField("expiry_date",    StringType(),  True),
    StructField("unit_cost_inr",  DoubleType(),  True),
    StructField("is_critical",    BooleanType(), True),
    StructField("updated_at",     StringType(),  True),
])

# Dispensing log row schema
DISPENSING_SCHEMA = StructType([
    StructField("dispense_id",         StringType(),  True),
    StructField("prescription_id",     StringType(),  True),
    StructField("patient_mrn",         StringType(),  True),
    StructField("ndc_code",            StringType(),  True),
    StructField("drug_name",           StringType(),  True),
    StructField("quantity_dispensed",  IntegerType(), True),
    StructField("pharmacist_id",       StringType(),  True),
    StructField("hospital_code",       StringType(),  True),
    StructField("dispensed_at",        StringType(),  True),
    StructField("lot_number",          StringType(),  True),
])

# Outer Debezium envelope schema
CDC_ENVELOPE_SCHEMA = StructType([
    StructField("payload", StructType([
        StructField("op",     StringType(),  True),
        StructField("source", StructType([
            StructField("table", StringType(), True),
            StructField("ts_ms", LongType(),   True),
            StructField("txId",  StringType(), True),
        ]), True),
        StructField("before", StringType(), True),   # JSON string — parse separately
        StructField("after",  StringType(), True),   # JSON string — parse separately
        StructField("ts_ms",  LongType(),   True),
    ]), True),
])


# ═══════════════════════════════════════════════════════════════════════════════
# FOREACHBATCH: CDC MERGE PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════════

def process_cdc_batch(batch_df, batch_id: int):
    """
    Process each CDC micro-batch using Delta MERGE:
    - op='c' (INSERT): Merge with notMatched -> INSERT
    - op='u' (UPDATE): Merge with matched -> UPDATE
    - op='d' (DELETE): Soft-delete flag (hard delete not done in Bronze)
    - op='r' (READ/snapshot): Treated as INSERT
    """
    if batch_df.isEmpty():
        print(f"[Pharmacy CDC] Batch {batch_id}: Empty. Skipping.")
        return

    batch_start = datetime.now(timezone.utc)
    total_count = batch_df.count()

    # Parse CDC envelope
    parsed = batch_df.select(
        from_json(col("value").cast("string"), CDC_ENVELOPE_SCHEMA).alias("cdc"),
        col("offset"),
        col("partition"),
        col("timestamp").alias("kafka_ts"),
    ).select(
        col("cdc.payload.op").alias("cdc_op"),
        col("cdc.payload.source.table").alias("src_table"),
        col("cdc.payload.source.ts_ms").alias("src_ts_ms"),
        col("cdc.payload.source.txId").alias("txn_id"),
        col("cdc.payload.after").alias("after_json"),
        col("cdc.payload.before").alias("before_json"),
        col("offset"),
        col("kafka_ts"),
    )

    # ── Inventory events (drug_inventory table) ────────────────────────────────
    inv_df = parsed.filter(col("src_table") == "drug_inventory")
    inv_count = inv_df.count()

    if inv_count > 0:
        inv_after = inv_df.filter(col("cdc_op").isin("c", "u", "r")).select(
            from_json(col("after_json"), INVENTORY_SCHEMA).alias("row"),
            col("cdc_op"),
            col("txn_id"),
            col("kafka_ts"),
        ).select(
            col("row.*"),
            col("cdc_op"),
            col("txn_id"),
            col("kafka_ts").alias("_kafka_ts"),
            lit(RUN_ID).alias("_run_id"),
            current_timestamp().alias("_load_ts"),
            lit(False).alias("_is_deleted"),
        )

        inv_delete = inv_df.filter(col("cdc_op") == "d").select(
            from_json(col("before_json"), INVENTORY_SCHEMA).alias("row"),
            col("txn_id"),
        ).select(col("row.inventory_id"), col("txn_id"))

        # MERGE insert/update records into inventory table
        if inv_after.count() > 0:
            if spark.catalog.tableExists(INVENTORY_TABLE):
                delta_tbl = DeltaTable.forName(spark, INVENTORY_TABLE)
                (
                    delta_tbl.alias("target")
                    .merge(inv_after.alias("src"), "target.inventory_id = src.inventory_id")
                    .whenMatchedUpdateAll()
                    .whenNotMatchedInsertAll()
                    .execute()
                )
                print(f"[Pharmacy CDC] MERGE {inv_after.count()} inventory rows → {INVENTORY_TABLE}")
            else:
                inv_after.write.format("delta").mode("append").saveAsTable(INVENTORY_TABLE)
                print(f"[Pharmacy CDC] Initial WRITE {inv_after.count()} inventory rows → {INVENTORY_TABLE}")

        # Soft-delete: set _is_deleted = True
        if inv_delete.count() > 0 and spark.catalog.tableExists(INVENTORY_TABLE):
            inv_delete.createOrReplaceTempView("inv_deletes_v")
            spark.sql(f"""
                MERGE INTO {INVENTORY_TABLE} AS target
                USING inv_deletes_v AS src
                ON target.inventory_id = src.inventory_id
                WHEN MATCHED THEN UPDATE SET target._is_deleted = TRUE, target._load_ts = current_timestamp()
            """)
            print(f"[Pharmacy CDC] Soft-deleted {inv_delete.count()} inventory rows")

        # Critical stock alert
        critical_df = inv_after.filter(col("is_critical") == True) if inv_after.count() > 0 else None
        if critical_df and critical_df.count() > 0:
            crit_rows = critical_df.select("drug_name", "hospital_code", "quantity_units", "reorder_level").limit(3).collect()
            crit_msg = "; ".join([f"{r['drug_name']} @ {r['hospital_code']}: qty={r['quantity_units']}, reorder={r['reorder_level']}" for r in crit_rows])
            send_alert(
                severity=SEVERITY_WARNING,
                title=f"💊 Critical Drug Stock Alert — {critical_df.count()} items",
                message=f"Batch {batch_id}: {crit_msg}",
                pipeline="10_Kafka_Pharmacy_CDC_Stream_NB",
                entity="pharmacy_inventory_stream",
            )

    # ── Dispensing events ──────────────────────────────────────────────────────
    disp_df = parsed.filter(col("src_table") == "dispensing_log")
    disp_count = disp_df.count()

    if disp_count > 0:
        disp_after = disp_df.filter(col("cdc_op") == "c").select(
            from_json(col("after_json"), DISPENSING_SCHEMA).alias("row"),
            col("txn_id"), col("kafka_ts"),
        ).select(
            col("row.*"),
            col("txn_id"),
            col("kafka_ts").alias("_kafka_ts"),
            lit(RUN_ID).alias("_run_id"),
            current_timestamp().alias("_load_ts"),
        )

        if disp_after.count() > 0:
            disp_after.write.format("delta").option("mergeSchema", "true").mode("append").saveAsTable(DISPENSE_TABLE)
            print(f"[Pharmacy CDC] ✅ {disp_after.count()} dispensing records → {DISPENSE_TABLE}")

    # Audit log
    batch_end = datetime.now(timezone.utc)
    write_audit_log(
        pipeline_name="PL_Kafka_Pharmacy_CDC_Stream",
        notebook_name="10_Kafka_Pharmacy_CDC_Stream_NB",
        run_id=f"{RUN_ID}-b{batch_id}",
        source_system="KAFKA_PHARMACY_CDC",
        entity_name="pharmacy_inventory,dispensing",
        records_read=total_count,
        records_written=inv_count + disp_count,
        records_rejected=0,
        status="SUCCESS",
        start_time=batch_start,
        end_time=batch_end,
    )
    print(f"[Pharmacy CDC] Batch {batch_id} complete. inv={inv_count} disp={disp_count}")


# ═══════════════════════════════════════════════════════════════════════════════
# LAUNCH
# ═══════════════════════════════════════════════════════════════════════════════

raw_cdc_stream = (
    spark.readStream
         .format("kafka")
         .options(**KAFKA_OPTIONS)
         .load()
)

query = (
    raw_cdc_stream
    .writeStream
    .foreachBatch(process_cdc_batch)
    .option("checkpointLocation", CHECKPOINT_PATH)
    .trigger(processingTime=TRIGGER_INTERVAL if STREAMING_MODE == "continuous" else None,
             once=(STREAMING_MODE == "batch"))
    .queryName("mediflow360_pharmacy_cdc_stream")
    .start()
)

print(f"[Pharmacy CDC] 🚀 Stream running. Query ID: {query.id}")
query.awaitTermination()
print("[Pharmacy CDC] Stream terminated cleanly.")
