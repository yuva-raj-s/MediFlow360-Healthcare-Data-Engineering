# Databricks Notebook: 20_governance_automation/Unity_Catalog_RBAC_Setup.py
# MediFlow360 — Fine-Grained Access Control (RBAC)
# Purpose: Automate permission management in Unity Catalog

%run ../07_notebooks/00_Helper_NB

def setup_rbac():
    print(f"[RBAC] Initializing permissions for catalog: {UC_CATALOG}")
    
    # 1. Create Groups (Simulated - in real world done via SCIM/Entra ID)
    # spark.sql("CREATE GROUP data_analysts")
    # spark.sql("CREATE GROUP data_scientists")
    
    # 2. Assign Permissions to Schemas
    
    # Analysts: Read-only access to GOLD (Aggregated KPIs)
    spark.sql(f"GRANT USAGE ON CATALOG {UC_CATALOG} TO `data_analysts`")
    spark.sql(f"GRANT USAGE ON SCHEMA {UC_CATALOG}.{UC_SCHEMA_GOLD} TO `data_analysts`")
    spark.sql(f"GRANT SELECT ON SCHEMA {UC_CATALOG}.{UC_SCHEMA_GOLD} TO `data_analysts`")
    
    # Scientists: Read access to SILVER (Cleansed/Masked) for model training
    spark.sql(f"GRANT USAGE ON SCHEMA {UC_CATALOG}.{UC_SCHEMA_SILVER} TO `data_scientists`")
    spark.sql(f"GRANT SELECT ON SCHEMA {UC_CATALOG}.{UC_SCHEMA_SILVER} TO `data_scientists`")
    
    # 3. Deny access to BRONZE (Raw/PII) for all except Engineers
    # By default, UC is secure-by-design (No access unless granted)
    
    print("✅ RBAC Protocol Applied: Gold -> Analysts, Silver -> Scientists.")

if __name__ == "__main__":
    setup_rbac()
