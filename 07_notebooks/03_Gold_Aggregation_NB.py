# Databricks Notebook: 03_Gold_Aggregation_NB.py
# MediFlow360 — Gold Layer KPI Aggregations
# Author: Rahul Nair (DA-001) | Version: 2.1 | Date: 2024-03-22
# Description: Generates final reporting tables for Power BI consumption.

%run ./00_Helper_NB

from pyspark.sql.functions import col, count, sum as spark_sum, avg, round as spark_round, when, lit, datediff, current_date, expr
from datetime import datetime, timezone

RUN_ID = f"gold-{datetime.now().strftime('%Y%m%d%H%M%S')}"
start_time = datetime.now(timezone.utc)
print(f"[Gold] Starting Aggregation | Run ID: {RUN_ID}")

try:
    # ---------------------------------------------------------
    # 1. READ SILVER DATA (Filtered for active records)
    # ---------------------------------------------------------
    dim_patient = spark.read.table(get_silver_table("dim_patient")).filter(col("is_current") == 1)
    dim_provider = spark.read.table(get_silver_table("dim_provider"))
    dim_hospital = spark.read.table(get_silver_table("dim_hospital"))
    fact_admissions = spark.read.table(get_silver_table("fact_admissions"))
    fact_claims = spark.read.table(get_silver_table("fact_claims")).filter(col("is_current") == 1)
    
    # ---------------------------------------------------------
    # 2. DAILY KPI SUMMARY (Hospital Level)
    # BR-002, BR-003, BR-005: Admissions, Readmissions, Financials
    # ---------------------------------------------------------
    print("[Gold] Calculating Daily KPI Summary...")
    
    # Admission metrics
    adm_metrics = fact_admissions.groupBy("hospital_code", "admission_date") \
        .agg(
            count("admission_id").alias("new_admissions"),
            spark_sum(when(col("discharge_date").isNotNull(), 1).otherwise(0)).alias("discharges"),
            avg(datediff(col("discharge_date"), col("admission_date"))).alias("avg_los_days")
        )
        
    # Readmission logic (30-day window)
    from pyspark.sql import Window
    import pyspark.sql.functions as F
    w = Window.partitionBy("global_patient_id").orderBy("admission_date")
    
    readm_calc = fact_admissions \
        .withColumn("prev_discharge", F.lag("discharge_date").over(w)) \
        .withColumn("days_since_discharge", datediff(col("admission_date"), col("prev_discharge"))) \
        .withColumn("is_readmission", when((col("days_since_discharge") <= 30) & (col("days_since_discharge") >= 0), 1).otherwise(0))
        
    readm_metrics = readm_calc.groupBy("hospital_code", "admission_date") \
        .agg(
            spark_sum("is_readmission").alias("readmission_count")
        )
        
    # Claims/Financial metrics
    fin_metrics = fact_claims.groupBy("hospital_code", "claim_date") \
        .agg(
            count("claim_id").alias("claims_submitted"),
            spark_sum(when(col("status") == 'APPROVED', 1).otherwise(0)).alias("claims_approved"),
            spark_sum(when(col("status") == 'DENIED', 1).otherwise(0)).alias("claims_denied"),
            spark_sum(col("approved_amount_inr")).alias("revenue_inr")
        )
        
    # Join metrics to form Daily KPI
    kpi_daily = adm_metrics \
        .join(readm_metrics, ["hospital_code", "admission_date"], "left") \
        .join(fin_metrics, adm_metrics.hospital_code == fin_metrics.hospital_code, "left") \
        .drop(fin_metrics.hospital_code) \
        .withColumnRenamed("admission_date", "kpi_date") \
        .fillna(0)
        
    # Calculate Rates
    kpi_daily = kpi_daily \
        .withColumn("readmission_rate_pct", spark_round((col("readmission_count") / col("new_admissions")) * 100, 2)) \
        .withColumn("denial_rate_pct", spark_round((col("claims_denied") / col("claims_submitted")) * 100, 2)) \
        .withColumn("pipeline_run_id", lit(RUN_ID)) \
        .withColumn("refreshed_at", current_timestamp())

    # Write to Gold
    kpi_daily.write.format("delta").mode("overwrite").saveAsTable(get_gold_table("kpi_daily_summary"))
    
    # Write to Synapse Analytics (Dedicated SQL Pool) via PolyBase
    # Requires ADLS Gen2 staging directory
    kpi_daily.write \
        .format("com.databricks.spark.sqldw") \
        .option("url", SYNAPSE_JDBC_URL) \
        .option("forwardSparkAzureStorageCredentials", "true") \
        .option("dbTable", "gold.kpi_daily_summary") \
        .option("tempDir", f"{ABFSS_PATH}/gold/synapse_temp/") \
        .mode("overwrite") \
        .save()

    print("[Gold] KPI Summary aggregation and Synapse load completed.")

    # ---------------------------------------------------------
    # 3. AUDIT LOGGING
    # ---------------------------------------------------------
    end_time = datetime.now(timezone.utc)
    write_audit_log("PL_Gold_Aggregation", "03_Gold_Aggregation_NB", RUN_ID, "SILVER", "gold.kpi_daily_summary", kpi_daily.count(), kpi_daily.count(), 0, "SUCCESS", start_time, end_time)

except Exception as e:
    print(f"[ERROR] {str(e)}")
    end_time = datetime.now(timezone.utc)
    write_audit_log("PL_Gold_Aggregation", "03_Gold_Aggregation_NB", RUN_ID, "SILVER", "gold.kpi_daily_summary", 0, 0, 1, "FAILED", start_time, end_time, str(e))
    send_alert(SEVERITY_CRITICAL, "Gold Aggregation Failed", str(e), "03_Gold_Aggregation_NB")
    raise e