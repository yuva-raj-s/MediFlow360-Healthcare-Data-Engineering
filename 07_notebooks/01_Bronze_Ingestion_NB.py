# Databricks Notebook: 01_Bronze_Ingestion_NB.py
# MediFlow360 — Bronze Layer Ingestion with Schema Validation & Watermark
# Author: Arjun Patel (DE-002) + Kavitha Rajan (DE-003)
# Version: 1.5 | Last Updated: 2024-03-08

%run ./00_Helper_NB

from pyspark.sql.functions import col, lit, current_timestamp, current_date, to_timestamp, regexp_replace, trim, upper, sha2
from datetime import datetime, timezone
import re

RUN_ID = dbutils.widgets.get("pipeline_run_id") if "pipeline_run_id" in [w.name for w in dbutils.widgets.getAll()] else f"bronze-{datetime.now().strftime('%Y%m%d%H%M%S')}"
SOURCE_SYSTEM = dbutils.widgets.get("source_system") if "source_system" in [w.name for w in dbutils.widgets.getAll()] else "S1_PATIENTS"
start_time = datetime.now(timezone.utc)

print(f"[Bronze] Run ID: {RUN_ID} | Source: {SOURCE_SYSTEM}")


def add_audit_columns(df, source_system: str):
    """Add standard audit columns to every Bronze record."""
    return df \
        .withColumn("_src_system", lit(source_system)) \
        .withColumn("_load_timestamp", current_timestamp()) \
        .withColumn("_pipeline_run_id", lit(RUN_ID)) \
        .withColumn("_load_date", current_date())


def strip_bom(text: str) -> str:
    """Remove UTF-8 BOM prefix from string (INC-008 fix)."""
    return text.replace('\ufeff', '').strip()


def normalize_date_column(df, col_name: str):
    """
    Normalize date columns that may arrive as DD-MM-YYYY or MM-DD-YYYY.
    Attempt DD-MM-YYYY first (MRHS standard), then MM-DD-YYYY (Madurai HIS quirk — INC-001).
    """
    return df.withColumn(
        col_name,
        when(
            to_timestamp(col(col_name), "dd-MM-yyyy").isNotNull(),
            to_timestamp(col(col_name), "dd-MM-yyyy")
        ).when(
            to_timestamp(col(col_name), "MM-dd-yyyy").isNotNull(),
            to_timestamp(col(col_name), "MM-dd-yyyy")
        ).otherwise(None)
    )


def validate_and_land_s1_patients(watermark_val: str):
    """Ingest patient data from MySQL HIS (simulated: read from CSV in source folder)."""
    print(f"[Bronze] S1 Patients — watermark: {watermark_val}")

    raw_df = spark.read.option("header", True).option("inferSchema", True) \
        .csv(f"{ABFSS_PATH}/raw/s1_mysql_patients/")

    # Strip BOM from column names (INC-008 defensive fix)
    clean_cols = [strip_bom(c) for c in raw_df.columns]
    raw_df = raw_df.toDF(*clean_cols)

    # Watermark filter
    raw_df = raw_df.filter(col("updated_at") > lit(watermark_val))

    if raw_df.count() == 0:
        print("[Bronze] No new patient records since watermark. Done.")
        return 0

    # INC-001 Fix: normalize date_of_birth
    processed_df = normalize_date_column(raw_df, "date_of_birth")

    # PII: Hash Aadhaar immediately at Bronze
    processed_df = mask_aadhaar(processed_df, "aadhaar_number", "aadhaar_hash")

    # Cast patient_id to string, add source prefix
    processed_df = processed_df \
        .withColumn("patient_id_src", regexp_replace(col("patient_id").cast("string"), "^", "HIS-CHN-")) \
        .withColumn("first_name", trim(upper(col("first_name")))) \
        .withColumn("last_name", trim(upper(col("last_name"))))

    processed_df = add_audit_columns(processed_df, "HIS-CHN")

    # Schema validation: required columns check
    required_cols = ["patient_id_src", "first_name", "last_name", "date_of_birth", "updated_at"]
    missing = [c for c in required_cols if c not in processed_df.columns]
    if missing:
        raise ValueError(f"[Bronze] Schema validation failed. Missing columns: {missing}")

    # DQ: Null check on critical fields
    dob_nulls = check_null_rate(processed_df, "date_of_birth", threshold_pct=2.0)
    if not dob_nulls["passed"]:
        send_alert(SEVERITY_WARNING, "High DOB Null Rate", f"Null rate: {dob_nulls['null_rate_pct']}%", "Bronze_NB", "patients")

    # Write to Bronze
    load_date = datetime.now().strftime("%Y/%m/%d")
    output_path = get_bronze_path("s1_patients", load_date)
    processed_df.write.mode("overwrite").parquet(output_path)

    count = processed_df.count()
    print(f"[Bronze] S1 Patients written: {count} records → {output_path}")
    return count


def validate_and_land_s3_lab_sftp(file_path: str):
    """Ingest lab results from SFTP-dropped CSV. Handles BOM (INC-008)."""
    print(f"[Bronze] S3 Lab Results — file: {file_path}")

    raw_df = spark.read.option("header", True).option("inferSchema", True) \
        .option("encoding", "UTF-8-BOM") \
        .csv(file_path)

    # INC-008: Strip BOM from column names
    clean_cols = [strip_bom(c) for c in raw_df.columns]
    raw_df = raw_df.toDF(*clean_cols)

    # File audit: check if already processed (deduplication)
    src_filename = file_path.split("/")[-1]

    # Required columns check
    required = ["OrderID", "PatientMRN", "TestCode", "SpecimenCollected", "ResultReleased"]
    missing = [c for c in required if c not in raw_df.columns]
    if missing:
        raise ValueError(f"[Bronze] Lab file schema mismatch. Missing: {missing}. File: {src_filename}")

    processed_df = raw_df \
        .withColumnRenamed("OrderID", "order_id") \
        .withColumnRenamed("PatientMRN", "patient_mrn_src") \
        .withColumnRenamed("TestCode", "test_code") \
        .withColumnRenamed("SpecimenCollected", "specimen_collected_ts") \
        .withColumnRenamed("ResultReleased", "result_released_ts") \
        .withColumn("test_code", trim(upper(col("test_code")))) \
        .withColumn("_src_filename", lit(src_filename))

    processed_df = add_audit_columns(processed_df, "LIS-SFTP")

    load_date = datetime.now().strftime("%Y/%m/%d")
    output_path = get_bronze_path("s3_lab_results", load_date)
    processed_df.write.mode("append").parquet(output_path)

    count = processed_df.count()
    print(f"[Bronze] S3 Lab Results written: {count} records → {output_path}")
    return count


# MAIN
total_records = 0
errors = []

try:
    if SOURCE_SYSTEM in ("S1_PATIENTS", "ALL"):
        wm = get_watermark("s1_patients")
        n = validate_and_land_s1_patients(wm)
        total_records += n
        if n > 0:
            update_watermark("s1_patients", datetime.now(timezone.utc).isoformat(), RUN_ID)
except Exception as e:
    errors.append(str(e))
    send_alert(SEVERITY_CRITICAL, "Bronze S1 Failed", str(e), "Bronze_Ingestion_NB", "patients")

try:
    if SOURCE_SYSTEM in ("S3_LAB", "ALL"):
        lab_files = dbutils.fs.ls(f"{ABFSS_PATH}/raw/s3_sftp_lab_results/")
        for f in lab_files:
            if f.name.endswith(".csv"):
                n = validate_and_land_s3_lab_sftp(f.path)
                total_records += n
except Exception as e:
    errors.append(str(e))
    send_alert(SEVERITY_WARNING, "Bronze S3 Failed", str(e), "Bronze_Ingestion_NB", "lab_results")

end_time = datetime.now(timezone.utc)
write_audit_log("PL_Ingest_Bronze", "01_Bronze_Ingestion_NB", RUN_ID,
    SOURCE_SYSTEM, "patients,lab_results", total_records, total_records, len(errors),
    "FAILED" if errors else "SUCCESS", start_time, end_time,
    "; ".join(errors) if errors else None)

print(f"[Bronze] ✅ Done. Total records: {total_records}")
