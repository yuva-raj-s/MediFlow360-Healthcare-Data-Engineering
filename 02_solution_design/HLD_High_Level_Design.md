# High-Level Design (HLD)
## MediFlow360 — Unified Patient Intelligence Platform
**Document ID**: MRHS-HLD-001 | **Version**: 1.2 | **Date**: January 15, 2024
**Author**: Vikram Krishnan (SA-001) | **Reviewed by**: Priya Sharma (DE-001)

---

## 1. Architecture Overview

MediFlow360 follows the **Azure Medallion Architecture** (Bronze → Silver → Gold) feeding into an Enterprise Data Warehouse:

```text
[7 SOURCE SYSTEMS]
S1:MySQL(SHIR) | S2:REST-API(OAuth2) | S3:SFTP | S4:CosmosDB | S5:PostgreSQL(CDC) | S6:SharePoint(Excel) | S7:IoT Hub
        |
        v
[AZURE DATA FACTORY]  — Orchestration Engine (10 Linked Services, 8 Pipelines)
        |
        v
[ADLS GEN2 — mrhsadlsprod]
  /bronze/  — Raw files, partitioned by source/date, immutable
[UNITY CATALOG]
  mediflow_prod.silver — Managed Delta Tables, Cleansed, SCD applied
  mediflow_prod.gold   — Managed Delta Tables, KPI aggregations
        |
        v
[DATABRICKS]  — Medallion Processing Engine (Unity Catalog, PySpark)
  Bronze → Silver (SCD1/2/3 + PII Masking Engine) → Gold (KPIs + DQ Engine)
[GOVERNANCE AUTOMATION]
  PII/PHI Scrubbing (Regex/Hashing) | Automated Optimization (Vacuum/Optimize)
        |
        v
[AZURE SYNAPSE ANALYTICS]  — Enterprise Serving Layer
  Dedicated SQL Pool (DW500c)
  Fact/Dim tables distributed via Hash and Replicate strategies
        |
        v
[POWER BI SERVICE]  — 5 Dashboard Pages (DirectQuery)
        |
        v (parallel)
[AZURE SQL DATABASE]  — Operational Metadata & Audit Logs only
[ALERTING]  — Azure Monitor → Logic Apps → Email + Teams
```

---

## 2. Azure Resource Inventory

| Resource | Name | Tier | Purpose |
|----------|------|------|---------|
| Resource Group | mrhs-rg-mediflow360 | N/A | Container |
| ADLS Gen2 | mrhsadlsprod | ZRS 50TB | Bronze/Silver/Gold |
| Azure Data Factory | mrhs-adf-prod | Standard | Orchestration |
| Databricks | mrhs-dbx-prod | Premium | PySpark |
| **Azure Synapse Analytics** | **mrhs-synw-prod** | **DW500c** | **Data Warehouse Serving** |
| Azure SQL Database | mrhs-sqldb-meta | Basic 100DTU| Audit & Metadata |
| Azure Key Vault | mrhs-kv-prod | Standard | Secrets |
| Logic Apps | mrhs-la-alerts | Consumption | Notifications |
| Azure IoT Hub | mrhs-iothub-prod | Standard | ICU vitals |

**Total estimated monthly cost: ~$9,200 (Enterprise Scale)**

---

## 3. Data Flow Patterns

### Full Load (Day 1 only)
Source → ADF full extract → ADLS Bronze → Silver (full SCD load) → Gold → Azure SQL

### Incremental (Daily/Hourly)
Watermark read → ADF extracts delta → Bronze partition → Silver MERGE + SCD-2 expire/insert → Gold re-aggregate → Azure SQL UPSERT

### Event-Driven (Lab SFTP)
File dropped → ADF blob trigger → atomic move to /processing/ → Bronze_NB → archive → Silver → Gold

### IoT Micro-Batch (ICU Vitals — 5 min)
Bedside monitor → IoT Hub → Event Hub → ADF Tumbling Window → Bronze → Silver (15-min summary) → Gold

---

## 4. Security Architecture

- All secrets in **Azure Key Vault** (zero hardcoded credentials)
- **Managed Identity** for ADF → Key Vault auth
- **Governance**: Unity Catalog manages fine-grained RBAC (Data Analysts granted SELECT on gold schemas)
- **PII Masking**: Centralized **PII Masking Engine** (Regex-based email masking + deterministic hashing)
- **Metadata Lineage**: Every record injected with `_run_id`, `_load_ts`, and `_source_system` columns.
- **Data Quality**: Metadata-driven DQ engine halts pipelines on critical schema/constraint violations.

---

## 5. Disaster Recovery

| Component | RPO | RTO | Strategy |
|-----------|-----|-----|---------|
| ADLS Bronze | 24 hrs | 4 hrs | Re-run from source |
| Azure SQL Gold | 1 hr | 2 hrs | Point-in-time restore (7d) |
| ADF Pipelines | N/A | 1 hr | ARM template CI/CD redeploy |
| Databricks NB | N/A | 30 min | Git-versioned |

---
*MRHS Confidential | HLD v1.2*
