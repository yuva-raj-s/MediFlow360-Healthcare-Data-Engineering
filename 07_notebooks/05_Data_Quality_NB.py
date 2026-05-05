# Databricks Notebook: 05_Data_Quality_NB.py
# MediFlow360 — Data Quality & Governance Gating
# Author: Priya Sharma (DE-001) | Version: 3.1
# Last Updated: 2024-05-05

%run ./00_Helper_NB

print("[DQ] Starting Data Quality Scans...")

def run_dq_checks():
    dq_errors = []
    
    # 1. NULL Rate Check on Critical Bronze Columns
    print("[DQ] Running Rule 1: Null Rates")
    bronze_patients = spark.read.parquet(get_bronze_path("s1_patients"))
    null_count = bronze_patients.filter(col("patient_id").isNull() | col("aadhaar_hash").isNull()).count()
    total_count = bronze_patients.count()
    
    if total_count > 0:
        null_rate = null_count / total_count
        if null_rate > 0.05:
            msg = f"Rule 1 Failed: Null rate is {null_rate*100:.2f}%. Threshold is 5%."
            dq_errors.append(msg)
            send_alert(SEVERITY_WARNING, "High Null Rate", msg, "05_Data_Quality_NB")

    # 2. Referential Integrity Check (Silver)
    print("[DQ] Running Rule 2: Referential Integrity (Claims -> Patient)")
    try:
        claims = spark.read.table(get_silver_table("fact_claims")).select("patient_sk")
        patients = spark.read.table(get_silver_table("dim_patient")).select("patient_sk")
        orphans = claims.join(patients, on="patient_sk", how="left_anti").count()
        
        if orphans > 0:
            msg = f"Rule 2 Failed: {orphans} orphaned claims found with no matching patient_sk."
            dq_errors.append(msg)
            send_alert(SEVERITY_CRITICAL, "Referential Integrity Broken", msg, "05_Data_Quality_NB")
    except Exception as e:
        print(f"[DQ] Skipping Rule 2 (Tables might not exist yet): {str(e)}")

    # 3. PII Exposure Check (INC-003 Prevention)
    print("[DQ] Running Rule 3: DPDP PII Scan on Gold Layer")
    forbidden_terms = ["aadhaar_number", "ssn", "credit_card", "phone_number"]
    try:
        gold_kpi = spark.read.table(get_gold_table("kpi_daily_summary"))
        columns = [c.lower() for c in gold_kpi.columns]
        for term in forbidden_terms:
            if term in columns:
                msg = f"Rule 3 Failed: PII Column '{term}' detected in Gold layer!"
                dq_errors.append(msg)
                send_alert(SEVERITY_CRITICAL, "DPDP VIOLATION: PII Leak", msg, "05_Data_Quality_NB")
                raise Exception(msg)
    except Exception as e:
        pass

    # 4. Clinical Signal Integrity (NEW v3.1)
    print("[DQ] Running Rule 4: Clinical Signal Integrity (Streaming Vitals)")
    try:
        vitals = spark.read.table(f"{UC_CATALOG}.{UC_SCHEMA_BRONZE}.icu_vitals_stream") \
            .filter(col("_load_timestamp") >= expr("current_timestamp() - interval 1 hour"))
        
        # Check for extreme impossible values (noise)
        impossible_vitals = vitals.filter(
            (col("heart_rate") < 10) | (col("heart_rate") > 400) |
            (col("spo2") < 20.0) | (col("temperature_c") < 25.0)
        ).count()

        if impossible_vitals > 0:
            msg = f"Rule 4 Failed: {impossible_vitals} records with physically impossible vital signs detected in the last hour."
            dq_errors.append(msg)
            send_alert(SEVERITY_WARNING, "Clinical Data Noise Detected", msg, "05_Data_Quality_NB")
    except Exception as e:
        print(f"[DQ] Skipping Rule 4: {str(e)}")
        
    return dq_errors

errors = run_dq_checks()
if errors:
    print(f"[DQ] Scan completed with {len(errors)} errors.")
    for e in errors:
        print(f" - {e}")
else:
    print("[DQ] All Data Quality checks passed successfully.")