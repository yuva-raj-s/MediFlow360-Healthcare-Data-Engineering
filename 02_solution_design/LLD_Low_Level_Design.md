# Low-Level Design (LLD)
## MediFlow360 — Unified Patient Intelligence Platform
**Document ID**: MRHS-LLD-001 | **Version**: 2.0
**Architect**: Vikram Krishnan (SA-001) | **Data Engineer**: Priya Sharma (DE-001)

---

## 1. System Overview
This Low-Level Design (LLD) details the granular implementation specifics for the MediFlow360 data platform, transitioning from 7 disparate operational sources through Azure Data Factory (ADF), Databricks (Medallion processing), and finally into Azure Synapse Analytics for enterprise-scale serving. 

---

## 2. Azure Data Factory (ADF) Orchestration Deep-Dive

### 2.1 Master Orchestrator Pipeline (`PL_Master_Orchestrator`)
The orchestration follows a dynamic metadata-driven approach to minimize pipeline sprawl.
1. **Trigger**: `TRG_Daily_01AM` (Scheduled Event).
2. **Lookup Activity (`LKP_Get_Watermarks`)**:
   - Queries `bronze_meta.sp_get_watermark` on Azure SQL DB.
   - Retrieves the last processed `updated_at` or `claim_date` for all 7 active sources.
3. **ForEach Activity (`FE_Ingest_Sources`)**:
   - Iterates sequentially (or parallel max concurrency = 4) over the lookup output array.
   - **Inside ForEach**: Execute Pipeline (`EP_Ingest_Specific_Source`) dynamically bound to `@item().source_name`.
4. **Conditional Execution (`IF_All_Success`)**:
   - Evaluates if all sources ingested successfully into the ADLS Gen2 `/bronze/` container.
   - **True**: Triggers Databricks Silver processing.
   - **False**: Triggers `mrhs-la-email-alert` (Logic App) via a Web Activity POST request with error payload.

### 2.2 Ingestion Patterns per Source
| Source | Pattern | Copy Activity Source Settings | Sink Settings (Bronze) |
|--------|---------|-------------------------------|------------------------|
| **S1: MySQL** | Watermark | `SELECT * FROM patients WHERE updated_at > '@{pipeline().parameters.LastWatermark}'` | Format: Parquet. Partition: `s1_patients/YYYY/MM/DD/` |
| **S2: REST API**| Pagination| Relative URL: `?page={offset}`. Pagination Rule: `$.meta.nextPageUrl` | Format: JSON. Partition: `s2_claims/YYYY/MM/DD/` |
| **S3: SFTP** | File Event| Trigger: `TRG_BlobEvents_Lab`. Filter: `*.csv`. Strip BOM prefix. | Format: Parquet. Partition: `s3_lab_results/YYYY/MM/DD/` |
| **S5: PostgreSQL**| CDC / WAL | Logical replication slot: `adf_pharmacy_slot`. | Format: Parquet. Schema captures `__op` (Insert/Update/Delete). |

---

## 3. Databricks Execution Hierarchy & Cluster Config

### 3.1 Cluster Configuration (Jobs Cluster)
- **Runtime**: 13.3 LTS (Spark 3.4.1, Scala 2.12)
- **Node Type**: `Standard_DS3_v2` (14GB Memory, 4 Cores)
- **Scaling**: Autoscale enabled (Min: 2, Max: 8 workers).
- **VNet Injection**: Deployed within a secure VNet subnet; no public IP for worker nodes.

### 3.2 Notebook Sequence
All notebooks are orchestrated via Databricks Workflows (triggered by ADF upon Bronze completion).

1. **`00_Helper_NB`**:
   - Attached via `%run` in all subsequent notebooks.
   - Injects global variables, custom Python logger class, and establishes Unity Catalog ABFSS configurations via Service Principals to eliminate legacy DBFS mounts.
2. **`01_Bronze_Ingestion_NB`**:
   - Reads incremental loads from ADLS Gen2 using direct `abfss://` paths.
   - Enforces schema validation using PySpark `StructType`.
   - Hashes sensitive PII (Aadhaar, Phone) using `pyspark.sql.functions.sha2`.
3. **`02b_Silver_SCD2_NB`**:
   - Performs Hash-based CDC against the existing Unity Catalog Managed Delta Tables (`catalog.silver.table`).
   - Uses `DeltaTable.merge()` to implement SCD Type 2 logic (expiring old rows by setting `is_current = False` and `eff_end_date = current_timestamp()`, while inserting new rows).
4. **`03_Gold_Aggregation_NB`**:
   - Reads pristine Silver data from Unity Catalog to generate business KPIs.
   - Calculates 30-day readmission rates, claims TAT, and ICU vitals roll-ups using window functions.
   - Writes directly to Unity Catalog Gold Managed Delta Tables, preparing them for Synapse PolyBase loading.

---

## 4. Azure Synapse Analytics Integration

Synapse Analytics acts as the enterprise Data Warehouse serving layer, directly fed by Databricks Gold output.

### 4.1 Synapse Workspace & Dedicated SQL Pool
- **Compute Scale**: DW100c (Development) / DW500c (Production).
- **Data Loading Pattern (PolyBase / COPY INTO)**:
  Databricks exports Gold aggregates into an ADLS staging directory. Synapse triggers a `COPY INTO` command to bulk-load data at massive parallel scale.

### 4.2 Table Distribution Strategy
To guarantee sub-second query latency for Power BI DirectQuery, Synapse tables follow strict distribution strategies:
- **`dim_patient` (SCD2)**: `REPLICATE` distribution (approx. 5M rows). Duplicated across all compute nodes to eliminate data movement during joins.
- **`dim_physician`**: `REPLICATE` distribution.
- **`fact_claims`**: `HASH(patient_id)` distribution. Given 50M+ rows, hashing on patient ID ensures even data skew and colocates claim records with the patient dimension (if hashed similarly).
- **`fact_icu_vitals`**: `HASH(device_id)` distribution with Clustered Columnstore Index (CCI).

### 4.3 Synapse Row-Level Security (RLS)
- Integrated with Microsoft Entra ID (Azure AD).
- Implemented inline Table Valued Functions (TVFs) ensuring that Hospital Admins can only query records where `hospital_code = @UserHospital`.

---

## 5. Metadata and Audit Tracking (Azure SQL DB)

While Synapse handles heavy analytical queries, Azure SQL Database (Basic Tier) remains for operational metadata.
- **`bronze_meta.watermark_table`**: Stores the high-watermark for each pipeline run.
- **`mrhs_audit.pipeline_logs`**: Captures granular `pipeline_run_id`, `records_read`, `records_written`, and `error_message`. Queried by operational dashboards to track pipeline health.

---
*MRHS Confidential | Low-Level Design v2.0*