# Project Charter
## MediFlow360 — Unified Patient Intelligence Platform
**Document ID**: MRHS-PC-001 | **Version**: 2.0 (Enterprise Scale) | **Date**: February 26, 2024
**Prepared by**: Sneha Iyer (PM-001) | **Approved by**: Ms. Divya Anand (CIO)

---

## 1. Project Purpose

MediCare Regional Health System (MRHS) currently operates 4 hospitals with siloed data systems. Each hospital uses independent software for patient management, pharmacy, labs, and billing. There is no single source of truth, making it impossible to track patient journeys across facilities, detect revenue leakage, or measure clinical quality at the network level.

**MediFlow360** is the enterprise data & analytics platform that unifies all data streams. Phase 1 successfully demonstrated the Medallion architecture using Azure SQL. **Phase 2 (Current)** scales this architecture to handle petabyte-level analytic workloads using **Azure Synapse Analytics** to ensure sub-second latency for executive dashboards and advanced analytics.

---

## 2. Project Objectives

1. Ingest data from **7 heterogeneous source systems** into a centralised Azure Data Lake (ADLS Gen2).
2. Transform raw data through a **Bronze → Silver → Gold** medallion architecture using Databricks.
3. Migrate the Serving Layer to **Azure Synapse Analytics (Dedicated SQL Pools)** to provide Massively Parallel Processing (MPP) for high-concurrency Power BI consumption.
4. Implement **SCD Type 1, 2 & 3** for historical accuracy across patient, provider, and drug dimensions.
5. Deliver **16 automated alerts** across pipeline health, data quality, and business KPIs.
6. Achieve full compliance with **India DPDP Act 2023** and **NABH accreditation** data requirements.

---

## 3. Scope

### In Scope
- Ingestion pipelines for S1–S7 source systems via Azure Data Factory.
- Databricks notebooks for Bronze, Silver, Gold transformation and PII masking.
- Azure Synapse Analytics Workspace and Dedicated SQL Pool deployment.
- PolyBase / COPY INTO loading mechanisms from ADLS Gold to Synapse.
- Azure Monitor alerts + Logic Apps notifications (Teams + Email).
- Power BI dashboards (Executive KPI, Clinical Quality, Claims Analytics) connected via Synapse DirectQuery.
- Full audit logging and data lineage tracking in Azure SQL DB.

### Out of Scope
- Real-time streaming (stream processing — deferred to Phase 3).
- Mobile application for clinicians.
- Integration with external insurance APIs.

---

## 4. Deliverables

| # | Deliverable | Due Date | Owner |
|---|-------------|----------|-------|
| D1 | ADF Ingestion Pipelines (7 sources) | Feb 16, 2024 | DE-002 |
| D2 | Bronze Layer notebooks + validation | Feb 23, 2024 | DE-003 |
| D3 | Silver Layer SCD notebooks | Mar 8, 2024 | DE-003 |
| D4 | Gold Layer aggregation notebooks | Mar 22, 2024 | DE-001 |
| D5 | **Azure Synapse Analytics Provisioning** | Apr 01, 2024 | SA-001 |
| D6 | **Synapse PolyBase Load & Distribution** | Apr 15, 2024 | DE-001 |
| D7 | Power BI dashboards (Synapse DirectQuery)| May 10, 2024 | DA-001 |
| D8 | Data governance & DPDP documentation | May 17, 2024 | DG-001 |
| D9 | CI/CD pipeline (Azure DevOps) | May 31, 2024 | OPS-001 |
| D10 | UAT sign-off from stakeholders | Jul 15, 2024 | PM-001 |
| D11 | Go-live | Jul 31, 2024 | All |

---

## 5. Budget & Resources (Enterprise Scale)

| Resource | Unit | Qty | Est. Monthly Cost |
|----------|------|-----|-------------------|
| Azure ADLS Gen2 | Storage | 50 TB | $1,000 |
| Azure Data Factory | Activities | 500/day | $50 |
| Azure Databricks | DBU | Auto | $2,500 |
| **Azure Synapse Analytics** | DW500c | 1 pool | **$5,500** |
| Azure SQL Database | S3 (100 DTU) | 1 instance| $150 |
| Azure Key Vault | Secrets | 50 | $2 |
| **Total Azure Cost** | | | **~$9,202/month** |

---

## 6. Risks & Mitigations

| Risk ID | Risk Description | Probability | Impact | Mitigation |
|---------|-----------------|-------------|--------|------------|
| R-001 | SHIR for MySQL goes offline | Medium | High | Auto-restart service, alert ALT-001 |
| R-002 | **Synapse compute cost overrun** | High | High | Auto-pause schedule during off-hours |
| R-003 | PII data exposure in Synapse | Low | Critical | Synapse RLS + Dynamic Data Masking |
| R-004 | Source API breaking change | Medium | High | Schema validation at Bronze ingestion |

---

## 7. Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| CIO (Sponsor) | Ms. Divya Anand | ✅ Approved | 2024-02-26 |
| CFO | Mr. Balaji Venkatesh | ✅ Approved | 2024-02-26 |
| CMO | Dr. Meena Krishnaswamy | ✅ Approved | 2024-02-26 |
| Solution Arch | Vikram Krishnan | ✅ Approved | 2024-02-26 |

---
*MRHS Confidential | Project Charter | v2.0*
