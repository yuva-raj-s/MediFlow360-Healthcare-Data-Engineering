# RACI Matrix — MediFlow360
**Document ID**: MRHS-RACI-001 | **Version**: 1.0 | **Date**: January 8, 2024

**R** = Responsible | **A** = Accountable | **C** = Consulted | **I** = Informed

---

## Workstream 1 — Infrastructure & DevOps

| Activity | DE-001 | DE-002 | DE-003 | DE-004 | DA-001 | PM-001 | SA-001 | DG-001 | OPS-001 | CIO |
|----------|--------|--------|--------|--------|--------|--------|--------|--------|---------|-----|
| Azure resource provisioning | C | C | | | | I | A | | R | I |
| SHIR installation & management | | C | | | | I | A | | R | I |
| Key Vault secret management | C | | | | | I | A | | R | |
| CI/CD pipeline (Azure DevOps) | C | C | | | | I | A | | R | I |
| Azure Monitor alert setup | C | | | | | I | A | | R | I |
| Cost monitoring & reporting | | | | | | I | C | | R | A |

---

## Workstream 2 — Data Ingestion (ADF)

| Activity | DE-001 | DE-002 | DE-003 | DE-004 | DA-001 | PM-001 | SA-001 | DG-001 | OPS-001 |
|----------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| ADF linked services (all 10) | A | R | | | | I | C | | C |
| Pipeline: MySQL S1 (SHIR) | A | R | | | | I | C | | C |
| Pipeline: REST API S2 (OAuth2) | A | R | | | | I | C | | |
| Pipeline: SFTP S3 (Lab files) | A | R | | | | I | C | | |
| Pipeline: MongoDB S4 | A | R | | | | I | C | | |
| Pipeline: PostgreSQL S5 (CDC) | A | R | | | | I | C | | |
| Pipeline: SharePoint S6 (Excel) | A | R | | | | I | C | | |
| Pipeline: IoT Hub S7 (Vitals) | A | R | C | | | I | C | | C |
| Watermark table management | A | R | C | | | I | C | | |
| Pipeline failure retry logic | C | R | | | | I | A | | C |

---

## Workstream 3 — Databricks Notebooks

| Activity | DE-001 | DE-002 | DE-003 | DE-004 | DA-001 | PM-001 | SA-001 | DG-001 |
|----------|--------|--------|--------|--------|--------|--------|--------|--------|
| Helper_NB (shared utilities) | A | C | R | | | I | C | |
| Bronze_Ingestion_NB | A | C | R | C | | I | C | |
| Silver_Transform_NB (SCD1) | A | | R | C | | I | C | C |
| Silver_SCD2_NB | A | | R | | | I | C | C |
| Silver_SCD3_NB | A | | R | | | I | C | C |
| Gold_Aggregation_NB | R | | C | | C | I | A | |
| Anomaly_Detection_NB | R | | C | | C | I | A | |
| Data_Quality_NB | A | | R | R | C | I | C | C |
| Alert_Dispatcher_NB | C | C | R | | | I | A | |
| Watermark_Manager_NB | A | C | R | | | I | C | |

---

## Workstream 4 — Data Governance

| Activity | DE-001 | DE-002 | DE-003 | DE-004 | DA-001 | PM-001 | SA-001 | DG-001 | CIO | Compliance |
|----------|--------|--------|--------|--------|--------|--------|--------|--------|-----|------------|
| PII classification | C | | C | | | I | C | R | A | C |
| Data masking enforcement | C | | R | | | I | C | A | I | C |
| DPDP compliance checklist | | | | | | C | C | R | A | C |
| Data retention policy | C | | | | | C | C | R | A | C |
| Access control matrix | C | | | | | I | C | R | A | |
| Audit table review | C | | C | R | | I | | A | | C |

---

## Workstream 5 — Analytics & Reporting

| Activity | DE-001 | DE-002 | DE-003 | DE-004 | DA-001 | PM-001 | SA-001 | DG-001 |
|----------|--------|--------|--------|--------|--------|--------|--------|--------|
| Gold layer views (SQL) | A | | C | R | C | I | C | |
| DAX measures library | | | | | R | I | | |
| Executive KPI dashboard | C | | | | R | I | A | |
| Clinical Quality dashboard | C | | | | R | I | A | |
| Claims Analytics dashboard | | | | | R | I | A | |
| Pharmacy dashboard | | | | | R | I | A | |
| ICU Operations dashboard | | | | | R | I | A | |
| Dashboard publish & share | | | | | R | A | | |
| Stakeholder demo preparation | | | | | C | R | | |

---

## Workstream 6 — Testing & Quality

| Activity | DE-001 | DE-002 | DE-003 | DE-004 | DA-001 | PM-001 | SA-001 | DG-001 |
|----------|--------|--------|--------|--------|--------|--------|--------|--------|
| Unit test cases (notebooks) | A | C | R | R | | I | C | |
| Integration test (end-to-end) | A | R | R | R | | C | C | |
| Data quality test execution | A | | C | R | C | I | | C |
| UAT coordination | C | | | | C | R | | A |
| UAT sign-off | | | | | | A | | R |
| Performance benchmarking | C | R | | | | I | A | |

---
*MRHS Confidential | RACI Matrix | v1.0*
