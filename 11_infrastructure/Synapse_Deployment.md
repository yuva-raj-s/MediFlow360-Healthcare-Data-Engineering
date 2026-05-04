# Azure Synapse Analytics Deployment Guide
**Document ID**: MRHS-INFRA-005 | **Owner**: SA-001

---

## 1. Overview
As part of the Phase 2 Enterprise architecture, MediFlow360 utilizes Azure Synapse Analytics (Dedicated SQL Pool) as the serving layer for Power BI. This document outlines the provisioning steps, distribution strategy, and PolyBase loading mechanisms.

---

## 2. Resource Provisioning
We provision the workspace and pool using Azure CLI / ARM templates.

### 2.1 Azure CLI Commands
```bash
# Variables
RG="mrhs-rg-mediflow360"
SYN_WORKSPACE="mrhs-synw-prod"
SQL_POOL="mrhs-sqlpool-gold"

# Create Synapse Workspace
az synapse workspace create \
  --name $SYN_WORKSPACE \
  --resource-group $RG \
  --storage-account mrhsadlsprod \
  --file-system synapse \
  --sql-admin-login-user "mrhs_admin" \
  --sql-admin-login-password "KeyVaultSecret" \
  --location "southindia"

# Create Dedicated SQL Pool (DW500c)
az synapse sql pool create \
  --name $SQL_POOL \
  --workspace-name $SYN_WORKSPACE \
  --performance-level DW500c
```

---

## 3. Table Distribution Strategy
To guarantee sub-second query latency for Power BI DirectQuery, we enforce strict distribution keys:

| Table Name | Type | Distribution | Justification |
|------------|------|--------------|---------------|
| `dim_patient` | Dimension | `REPLICATE` | ~5M rows. Duplicated across all 60 compute nodes to eliminate data movement during joins. |
| `dim_provider` | Dimension | `REPLICATE` | Small table, queried frequently. |
| `fact_claims` | Fact | `HASH(patient_id)` | ~50M rows. Hashed on `patient_id` to colocate claim records with the patient dimension (if hashed similarly) and ensure even data skew. |
| `fact_admissions`| Fact | `HASH(hospital_code)`| Prevents skew during hospital-level KPI aggregations. |

---

## 4. PolyBase Loading Pattern (Databricks)
Databricks Gold notebooks use the `com.databricks.spark.sqldw` connector.

### Prerequisites
1. **Managed Identity**: The Synapse Workspace MSI must have `Storage Blob Data Contributor` access to the ADLS Gen2 `/gold/` container.
2. **Staging Directory**: Databricks requires a temporary staging directory in ADLS.

### Execution Flow
1. Databricks writes Parquet files to the temporary staging directory (`/gold/synapse_temp/`).
2. Databricks issues a `COPY INTO` command to the Synapse Control Node.
3. Synapse Compute Nodes use PolyBase to ingest the Parquet chunks in parallel directly from ADLS.
4. Databricks cleans up the staging directory.

---
*MRHS Confidential | Infrastructure Docs | Synapse*
