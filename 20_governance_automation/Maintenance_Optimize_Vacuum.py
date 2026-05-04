# Databricks Notebook: 20_governance_automation/Maintenance_Optimize_Vacuum.py
# MediFlow360 — Delta Lake Optimization & Hygiene
# Purpose: Performance tuning and storage cost reduction

%run ../07_notebooks/00_Helper_NB

def run_maintenance(catalog="mediflow_prod"):
    """Automated maintenance for all tables in a catalog."""
    schemas = ["bronze", "silver", "gold"]
    
    for schema in schemas:
        print(f"[Maintenance] Processing schema: {schema}")
        tables_df = spark.catalog.listTables(f"{catalog}.{schema}")
        
        for table in tables_df:
            table_name = f"{catalog}.{schema}.{table.name}"
            print(f"  -> Optimizing table: {table_name}")
            
            # 1. OPTIMIZE (Compact files)
            spark.sql(f"OPTIMIZE {table_name}")
            
            # 2. VACUUM (Remove files older than 7 days)
            # Standard industry practice: retention period of 168 hours
            spark.sql(f"VACUUM {table_name} RETAIN 168 HOURS")
            
            print(f"  [DONE] {table_name} is clean.")

# Note: In production, Z-ORDER should be applied to Join/Filter keys.
# spark.sql("OPTIMIZE silver.patients ZORDER BY (patient_id)")

if __name__ == "__main__":
    run_maintenance()
