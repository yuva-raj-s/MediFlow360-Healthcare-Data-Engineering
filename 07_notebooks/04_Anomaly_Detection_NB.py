# Databricks Notebook: 04_Anomaly_Detection_NB.py
# MediFlow360 — Fraud Scoring + Clinical Anomaly Detection
# Author: Priya Sharma (DE-001) | Version: 1.2 | Date: 2024-04-01

%run ./00_Helper_NB

from pyspark.sql.functions import col, count, sum as spark_sum, avg, when, lit, datediff, current_date, to_date
from datetime import datetime, timezone

RUN_ID = f"anomaly-{datetime.now().strftime('%Y%m%d%H%M%S')}"
start_time = datetime.now(timezone.utc)
print(f"[Anomaly] Starting | Run ID: {RUN_ID}")

# ============================================================
# FRAUD SCORING — BR-006
# Rule F1: Same procedure billed >2x in 7 days → score +3
# Rule F2: Claim amount > 200000 INR → score +2
# Rule F3: Claim submitted <1hr after discharge → score +2
# Rule F4: Physician billed >30 procedures/day → score +2
# Rule F5: ICD-CPT mismatch → score +3
# ============================================================

def compute_fraud_scores():
    print("[Anomaly] Computing fraud scores...")
    claims = spark.read.table(get_silver_table("fact_claims")).filter(col("is_current") == 1)

    if claims.count() == 0:
        print("[Anomaly] No claims in silver. Skipping.")
        return 0

    from pyspark.sql import Window
    import pyspark.sql.functions as F
    w7 = Window.partitionBy("patient_sk", "procedure_code").orderBy("claim_date") \
              .rangeBetween(-6, 0)

    # Rule F1: procedure billed >2x in 7-day window
    claims = claims.withColumn("proc_count_7d", count("claim_id").over(w7))
    claims = claims.withColumn("F1", when(col("proc_count_7d") > 2, 3).otherwise(0))

    # Rule F2: High value claim
    claims = claims.withColumn("F2", when(col("claim_amount_inr") > 200000, 2).otherwise(0))

    # Rule F3: Submitted < 1hr after claim date (proxy: submission same day)
    claims = claims.withColumn("F3", lit(0))  # Simplified; full logic needs discharge_ts

    # Rule F4: Physician billing >30 procedures/day
    phys_daily = claims.groupBy("physician_id", "claim_date") \
        .agg(count("claim_id").alias("daily_proc_count"))
    claims = claims.join(phys_daily, ["physician_id", "claim_date"], "left")
    claims = claims.withColumn("F4", when(col("daily_proc_count") > 30, 2).otherwise(0))

    # Rule F5: Simplified mismatch check (hardcoded pairs)
    INVALID_PAIRS = [("J06.9", "27447"), ("E11.9", "93000")]
    mismatch_cond = lit(False)
    for diag, proc in INVALID_PAIRS:
        mismatch_cond = mismatch_cond | ((col("diagnosis_code") == diag) & (col("procedure_code") == proc))
    claims = claims.withColumn("F5", when(mismatch_cond, 3).otherwise(0))

    # Total fraud score
    claims = claims.withColumn("fraud_score", col("F1") + col("F2") + col("F3") + col("F4") + col("F5"))

    # High-risk claims
    flagged = claims.filter(col("fraud_score") >= 5)
    flag_count = flagged.count()

    if flag_count > 0:
        send_alert(
            severity=SEVERITY_CRITICAL,
            title=f"Fraud Alert: {flag_count} High-Risk Claims Detected",
            message=f"Claims with fraud score ≥ 5 detected today. Immediate review required.",
            pipeline="Anomaly_Detection_NB",
            entity="fact_claims"
        )

    # Write fraud flags to Gold
    flagged.select(
        "claim_id", "fraud_score",
        col("F1").alias("rule_F1_triggered"), col("F2").alias("rule_F2_triggered"),
        col("F4").alias("rule_F4_triggered"), col("F5").alias("rule_F5_triggered"),
        col("claim_date").alias("flag_date")
    ).withColumn("pipeline_run_id", lit(RUN_ID)) \
     .write.format("delta").mode("append") \
     .saveAsTable(get_gold_table("fraud_flags"))

    print(f"[Anomaly] Fraud scoring done. {flag_count} high-risk flags.")
    return flag_count

# ============================================================
# READMISSION DETECTION — BR-003
# 30-day readmission: patient re-admitted within 30 days of discharge
# ============================================================

def detect_readmissions():
    print("[Anomaly] Detecting 30-day readmissions...")
    try:
        admissions = spark.read.table(get_silver_table("fact_admissions"))
    except Exception:
        print("[Anomaly] No admissions data yet. Skipping.")
        return 0

    from pyspark.sql import Window
    w = Window.partitionBy("global_patient_id").orderBy("admission_date")

    admissions = admissions \
        .withColumn("prev_discharge_date", F.lag("discharge_date").over(w)) \
        .withColumn("days_since_discharge", datediff(col("admission_date"), col("prev_discharge_date"))) \
        .withColumn("is_readmission", when((col("days_since_discharge") <= 30) & (col("days_since_discharge") >= 0), 1).otherwise(0))

    readmission_rate = admissions.agg(
        (spark_sum("is_readmission") / count("admission_id") * 100).alias("readmission_rate_pct")
    ).collect()[0]["readmission_rate_pct"] or 0.0

    print(f"[Anomaly] Readmission rate: {readmission_rate:.2f}%")

    if readmission_rate > 5.0:
        send_alert(SEVERITY_WARNING, f"High Readmission Rate: {readmission_rate:.1f}%",
                   "Weekly readmission rate exceeds NABH threshold of 5%.",
                   "Anomaly_Detection_NB", "readmissions")

    return readmission_rate

# ============================================================
# MAIN
# ============================================================
errors = []
try:
    flag_count = compute_fraud_scores()
except Exception as e:
    errors.append(str(e))
    send_alert(SEVERITY_WARNING, "Fraud Scoring Failed", str(e), "Anomaly_Detection_NB")

try:
    rr = detect_readmissions()
except Exception as e:
    errors.append(str(e))

end_time = datetime.now(timezone.utc)
write_audit_log("PL_Gold_Aggregation", "04_Anomaly_Detection_NB", RUN_ID,
    "GOLD", "fraud_flags,readmissions", 0, 0, len(errors),
    "FAILED" if errors else "SUCCESS", start_time, end_time,
    "; ".join(errors) if errors else None)

print(f"[Anomaly] Done.")
