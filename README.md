# MediFlow360 — Unified Patient Intelligence Platform
**MediCare Regional Health System (MRHS) | Enterprise Data & Analytics Platform**

---

## 🏥 Project Overview

**MediFlow360** is MRHS's enterprise data platform designed to dismantle data silos across the healthcare network. It ingests, transforms, and serves data from **7 heterogeneous source systems** across 4 hospitals into a unified **Medallion Architecture (Bronze → Silver → Gold)**. By leveraging the massively parallel processing (MPP) capabilities of **Azure Synapse Analytics**, MediFlow360 powers near real-time executive dashboards, clinical quality alerts, and revenue cycle fraud detection.

| Attribute | Value |
|-----------|-------|
| **Project Code** | MRHS-DE-2024-001 |
| **Start Date** | January 8, 2024 |
| **Target Go-Live** | July 31, 2024 |
| **Azure Region** | South India (Chennai) |
| **Scale** | Petabyte-scale (Synapse Analytics Serving) |
| **Status** | 🟢 In Progress (Sprint 3) |

---

## 🏗️ Enterprise Architecture Summary

The platform utilizes a modern Azure Data Stack, carefully orchestrated to ensure compliance (DPDP Act), high availability (99.9%), and sub-second analytical queries.

```text
[7 Heterogeneous Source Systems] 
 (MySQL, REST API, SFTP, CosmosDB, PostgreSQL CDC, SharePoint, IoT Hub)
         ↓
[Azure Data Factory (ADF) Orchestration]
         ↓
[ADLS Gen2: Bronze Layer] (Raw, Immutable, Partitioned)
         ↓
[Databricks: Silver Layer] (SCD Types 1/2/3, PII Masking, Cleansed)
         ↓
[Databricks: Gold Layer] (Aggregated KPIs, Fraud Scoring)
         ↓
[Azure Synapse Analytics: Dedicated SQL Pool] (Enterprise Serving Layer)
         ↓
[Power BI & Logic Apps] (Executive Dashboards & Clinical Alerts)
```

*(Note: Azure SQL Database is retained strictly for operational metadata and pipeline audit logging.)*

---

## 🗂️ Knowledge Base Structure

The project repository is structured as a comprehensive knowledge base for data engineers and architects.

```text
Hobby_Healthcare_Complex/
├── 00_project_charter/        Project goals, RACI, stakeholders, timeline
├── 01_business_requirements/  BRD v1+v2, FRD, NFR, Use Cases, RTM
├── 02_solution_design/        HLD, LLD, ADRs, Security Design
├── 03_data_dictionary/        Mapping docs, SCD design, incremental strategy
├── 04_onboarding/             New joiner guide, env setup, Azure provisioning
├── 05_data_governance/        PII matrix, DPDP compliance, access control
├── 06_source_data/            7 source folders + schema registry + sample data
├── 07_notebooks/              11 Databricks/PySpark notebooks
├── 08_sql_scripts/            DDL, DML, stored procedures, monitoring queries
├── 09_adf_pipelines/          ADF pipeline JSONs, linked services, triggers
├── 10_alerting/               Alert architecture, Azure Monitor rules, Logic Apps
├── 11_infrastructure/         Azure Synapse provisioning, cost optimization, DR plan
├── 12_testing/                Test strategy, unit/integration tests, UAT
├── 13_cicd/                   Azure DevOps YAML, deploy scripts
├── 14_runbooks/               Daily ops, incident response, on-call schedule
├── 15_incidents_and_struggles/ Real-world incidents with RCA documents
├── 16_change_requests/        Formal CRs with impact analysis
├── 17_meeting_notes/          Meeting records (kickoff → sprint retros)
├── 18_sprint_artifacts/       Sprint backlogs, product backlog, DoD
├── 19_power_bi/               Dashboard specs, DAX library, publish guide
└── MediFlow360_Interactive_Guide.html  ← INTERACTIVE PLATFORM PORTAL
```

---

## 🚀 Quick Start (Engineering Onboarding)

1. **Access the Portal**: Open `MediFlow360_Interactive_Guide.html` in your browser. This portal serves as the single pane of glass for all architecture diagrams and deployment sequences.
2. **Review the Medallion Implementation**: Read the Low-Level Design at `02_solution_design/LLD_Low_Level_Design.md`.
3. **Understand Security**: Review the Zero-Trust implementation in `02_solution_design/Security_Architecture.md`.
4. **Provision Azure Resources**: Execute the scripts located in `11_infrastructure/`.

---

## 🔌 Source Systems Integration (7 Types)

| ID | System | Technology | Entity | Integration Pattern |
|----|--------|------------|--------|---------------------|
| S1 | HIS Chennai | MySQL 8.0 (on-prem) | Patients, Admissions | ADF SHIR + Watermark |
| S2 | Insurance | REST API (OAuth2) | Claims, Approvals | ADF Pagination |
| S3 | LIS System | SFTP (CSV) | Lab Results | Blob Event Trigger |
| S4 | Appt. App | CosmosDB (JSON) | Appointments | Watermark Delta |
| S5 | Pharmacy | PostgreSQL 14 | Drug Inventory | Logical CDC (WAL) |
| S6 | HR Roster | SharePoint Excel | Staff Roster | Weekly Full Load |
| S7 | ICU Monitors | Azure IoT Hub | ICU Vitals | Tumbling Window |

---

## 👥 Core Engineering Team

| ID | Name | Role | Focus Area |
|----|------|------|------------|
| SA-001 | Vikram Krishnan | Solution Architect | Synapse, Overall Architecture |
| DE-001 | Priya Sharma | Lead Data Engineer | Databricks, Medallion Design |
| DE-002 | Arjun Patel | Senior DE | ADF Pipelines, SHIR |
| DE-003 | Kavitha Rajan | Data Engineer | PySpark Transformations |
| DA-001 | Rahul Nair | Senior Data Analyst | Power BI, Synapse DirectQuery|
| DG-001 | Lakshmi Venkat | Governance Officer| DPDP Compliance, Masking |

---

*MediFlow360 v2.0 | MRHS Enterprise Data & Analytics Platform | Highly Confidential*
