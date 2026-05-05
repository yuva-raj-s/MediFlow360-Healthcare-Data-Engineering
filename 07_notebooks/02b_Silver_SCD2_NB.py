# Databricks Notebook: 02b_Silver_SCD2_NB.py
# MediFlow360 — SCD Type 2: Full History Tracking
# Author: Kavitha Rajan (DE-003) | Reviewed: Priya Sharma (DE-001)
# Version: 1.5 | Last Updated: 2024-05-05
#
# ⚠️  INC-005 FIX: Watermark tracked on BRONZE _load_timestamp, NOT silver updated_at
#     See: 15_incidents_and_struggles/INC-005_SCD2_Broke_Incremental.md

%run ./00_Helper_NB

from pyspark.sql.functions import sha2, concat_ws, current_date, col, lit, current_timestamp, expr
from pyspark.sql.types import StringType
from datetime import datetime, timezone

# Widgets
dbutils.widgets.text("INGESTION_MODE", "batch")
INGESTION_MODE = dbutils.widgets.get("INGESTION_MODE").lower()

RUN_ID = f"scd2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
start_time = datetime.now(timezone.utc)

SCD2_PATIENT_TRACKED_COLS = ["address_line1", "city", "pincode", "insurance_plan_id"]
PATIENT_NK = "global_patient_id"


def apply_scd2_patients():
    """SCD-2 for dim_patient: expire old row, insert new version on attribute change."""
    print(f"[SCD2] Processing dim_patient (Mode: {INGESTION_MODE})...")

    # Patients (S1) is currently batch-only, but we'll respect the filter
    incoming = spark.read.parquet(get_bronze_path("s1_patients")) \
        .filter(col("_load_date") == current_date()) \
        .dropDuplicates([PATIENT_NK])

    if incoming.count() == 0:
        print("[SCD2] No patient delta today.")
        return 0, 0

    incoming = compute_record_hash(incoming, SCD2_PATIENT_TRACKED_COLS, "rec_hash_new")

    try:
        current_silver = spark.read.table(get_silver_table("dim_patient")) \
            .filter(col("is_current") == 1)
    except Exception:
        current_silver = None

    new_count = 0
    expired_count = 0

    if current_silver and current_silver.count() > 0:
        changed = incoming.alias("i").join(
            current_silver.alias("c"), col(f"i.{PATIENT_NK}") == col(f"c.{PATIENT_NK}"), "inner"
        ).filter(col("i.rec_hash_new") != col("c.record_hash"))

        expired_count = changed.count()

        if expired_count > 0:
            # Expire old rows
            changed.select(col("c.*")) \
                .withColumn("eff_end_date", current_date()) \
                .withColumn("is_current", lit(0)) \
                .write.format("delta").mode("append").saveAsTable(get_silver_table("dim_patient"))

            # Insert new versions
            changed.select(col("i.*")) \
                .withColumn("eff_start_date", current_date()) \
                .withColumn("eff_end_date", lit(None).cast("date")) \
                .withColumn("is_current", lit(1)) \
                .withColumn("record_hash", col("rec_hash_new")) \
                .drop("rec_hash_new") \
                .withColumn("created_by_run_id", lit(RUN_ID)) \
                .write.format("delta").mode("append").saveAsTable(get_silver_table("dim_patient"))

        # New patients (no existing Silver record)
        existing_keys = current_silver.select(PATIENT_NK)
        new_patients = incoming.join(existing_keys, PATIENT_NK, "left_anti")
    else:
        new_patients = incoming

    new_count = new_patients.count()
    if new_count > 0:
        new_patients \
            .withColumn("eff_start_date", current_date()) \
            .withColumn("eff_end_date", lit(None).cast("date")) \
            .withColumn("is_current", lit(1)) \
            .withColumn("record_hash", col("rec_hash_new")) \
            .drop("rec_hash_new") \
            .withColumn("created_by_run_id", lit(RUN_ID)) \
            .write.format("delta").mode("append").saveAsTable(get_silver_table("dim_patient"))

    print(f"[SCD2] dim_patient: {new_count} new, {expired_count} expired.")
    return new_count, expired_count


def apply_scd2_claims_status():
    """SCD-2 for fact_claims: each status transition creates a new history row."""
    print(f"[SCD2] Processing fact_claims status history (Mode: {INGESTION_MODE})...")

    if INGESTION_MODE == "streaming":
        # Read from Streaming Bronze Delta table
        bronze_claims = spark.read.table(f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.claims_stream") \
            .filter(col("_load_timestamp") >= expr("current_timestamp() - interval 1 day")) # Adaptive lookback
    else:
        # Read from Batch Bronze Parquet files
        bronze_claims = spark.read.parquet(get_bronze_path("s2_claims")) \
            .filter(col("_load_date") == current_date())

    bronze_claims = bronze_claims.dropDuplicates(["claim_id", "status"])

    if bronze_claims.count() == 0:
        return 0

    try:
        current_claims = spark.read.table(get_silver_table("fact_claims")) \
            .filter(col("is_current") == 1)
        new_transitions = bronze_claims.join(
            current_claims.select("claim_id", "status"), ["claim_id", "status"], "left_anti"
        )
    except Exception:
        new_transitions = bronze_claims

    count = new_transitions.count()
    if count > 0:
        new_transitions \
            .withColumn("eff_start_date", col("submission_ts").cast("date")) \
            .withColumn("eff_end_date", lit(None).cast("date")) \
            .withColumn("is_current", lit(1)) \
            .withColumn("created_by_run_id", lit(RUN_ID)) \
            .write.format("delta").mode("append").saveAsTable(get_silver_table("fact_claims"))

    print(f"[SCD2] fact_claims: {count} status transitions written.")
    return count


def apply_scd2_pharmacy_inventory():
    """SCD-2 for dim_pharmacy_inventory: merging logical CDC events from Kafka."""
    print(f"[SCD2] Processing dim_pharmacy_inventory (Mode: {INGESTION_MODE})...")

    if INGESTION_MODE == "streaming":
        bronze_cdc = spark.read.table(f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.pharmacy_cdc_stream")
    else:
        # Batch fallback if needed
        print("[SCD2] Pharmacy CDC is streaming only. Skipping batch run.")
        return 0

    # Process only 'u' (update) and 'c' (create) events
    # We ignore 'd' (delete) for SCD-2 history preservation or handle as 'is_deleted' flag
    incoming = bronze_cdc.filter(col("op").isin(["u", "c"])) \
        .select("item_id", "hospital_code", "stock_count", "reorder_level", "last_updated_at")

    if incoming.count() == 0:
        return 0

    silver_table = get_silver_table("dim_pharmacy_inventory")
    
    # Check if table exists
    try:
        spark.read.table(silver_table)
    except Exception:
        # Initialize table
        incoming.withColumn("eff_start_date", current_date()) \
                .withColumn("eff_end_date", lit(None).cast("date")) \
                .withColumn("is_current", lit(1)) \
                .withColumn("created_by_run_id", lit(RUN_ID)) \
                .write.format("delta").saveAsTable(silver_table)
        return incoming.count()

    # Append new versions
    incoming.withColumn("eff_start_date", current_date()) \
            .withColumn("eff_end_date", lit(None).cast("date")) \
            .withColumn("is_current", lit(1)) \
            .withColumn("created_by_run_id", lit(RUN_ID)) \
            .write.format("delta").mode("append").saveAsTable(silver_table)

    print(f"[SCD2] dim_pharmacy_inventory: {incoming.count()} CDC updates processed.")
    return incoming.count()


# MAIN
errors = []
total = 0

try:
    p, e = apply_scd2_patients()
    total += p + e
except Exception as ex:
    errors.append(str(ex))
    send_alert(SEVERITY_CRITICAL, "SCD2 Patient Failed", str(ex), "Silver_SCD2_NB")

try:
    c = apply_scd2_claims_status()
    total += c
except Exception as ex:
    errors.append(str(ex))
    send_alert(SEVERITY_WARNING, "SCD2 Claims Failed", str(ex), "Silver_SCD2_NB")

try:
    ph = apply_scd2_pharmacy_inventory()
    total += ph
except Exception as ex:
    errors.append(str(ex))
    send_alert(SEVERITY_WARNING, "SCD2 Pharmacy CDC Failed", str(ex), "Silver_SCD2_NB")

end_time = datetime.now(timezone.utc)
write_audit_log("PL_Silver_Transform", "02b_Silver_SCD2_NB", RUN_ID,
    "SILVER", "dim_patient,fact_claims,dim_pharmacy_inventory", total, total, len(errors),
    "FAILED" if errors else "SUCCESS", start_time, end_time,
    "; ".join(errors) if errors else None)

print(f"[SCD2] ✅ Done. Total records: {total}")

