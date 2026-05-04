# Databricks Notebook: 07_notebooks/05b_DQ_Metadata_Driven_NB.py
# MediFlow360 — Rules-Based Data Quality Engine
# Purpose: Decouple DQ rules from logic using a metadata-driven approach

%run ./00_Helper_NB

import json
from pyspark.sql.functions import col, expr

# Industry pattern: Load rules from a centralized JSON config (could also be a SQL table)
DQ_RULES_CONFIG = """
[
    {
        "table": "silver.dim_patient",
        "column": "date_of_birth",
        "rule_name": "valid_age",
        "condition": "date_of_birth < current_date()",
        "severity": "WARNING"
    },
    {
        "table": "silver.dim_patient",
        "column": "patient_id_src",
        "rule_name": "not_null",
        "condition": "patient_id_src IS NOT NULL",
        "severity": "CRITICAL"
    },
    {
        "table": "gold.kpi_daily_summary",
        "column": "total_patients",
        "rule_name": "positive_count",
        "condition": "total_patients >= 0",
        "severity": "CRITICAL"
    }
]
"""

def run_metadata_dq():
    rules = json.loads(DQ_RULES_CONFIG)
    overall_status = "PASS"
    
    for rule in rules:
        table_name = f"{UC_CATALOG}.{rule['table']}"
        print(f"[DQ Engine] Checking {table_name} -> {rule['rule_name']}")
        
        try:
            df = spark.read.table(table_name)
            failed_count = df.filter(f"NOT ({rule['condition']})").count()
            
            if failed_count > 0:
                msg = f"Rule '{rule['rule_name']}' failed for {failed_count} records in {table_name}"
                print(f"  ❌ {msg}")
                send_alert(rule['severity'], "DQ Rule Failure", msg, "DQ_Metadata_Driven_NB", rule['table'])
                
                if rule['severity'] == "CRITICAL":
                    overall_status = "FAIL"
            else:
                print(f"  ✅ Passed.")
        except Exception as e:
            print(f"  ⚠️ Skipping {table_name}: {str(e)}")

    if overall_status == "FAIL":
        raise Exception("Critical Data Quality violations detected. Pipeline halted.")

if __name__ == "__main__":
    run_metadata_dq()
