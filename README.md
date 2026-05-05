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
| **Status** | 🟢 In Progress (Sprint 4 — Kafka + Airflow) |

---

## 🏗️ Enterprise Architecture Summary (v3.0 — Kafka + Airflow)

```text
┌──────────────────── SOURCE SYSTEMS ───────────────────────────────────────┐
│  [BATCH]                           [REAL-TIME STREAMING]                   │
│  S1 MySQL Patients                 S7 ICU Monitors ──→ mrhs.icu.vitals     │
│  S3 SFTP Lab CSVs                  S2 Claims API   ──→ mrhs.insurance.claims│
│  S4 CosmosDB Appointments          S5 Pharmacy CDC ──→ mrhs.pharmacy.cdc   │
│  S6 SharePoint HR                                                          │
└──────────────┬─────────────────────────────┬──────────────────────────────┘
               │ ADF (SHIR + Watermark)       │ Azure Event Hubs (Kafka endpoint)
               ▼                              ▼
┌──────────────────── ORCHESTRATION: Apache Airflow (Astronomer/AKS) ───────┐
│  bronze_batch_ingestion  │  kafka_stream_monitor  │  silver/gold DAGs      │
└──────────────┬───────────────────────────────────────────────┬────────────┘
               ▼                                               ▼
┌────────────────── BRONZE LAYER (ADLS Gen2) ───────────────────────────────┐
│   Batch: patients, lab_results, appointments, staff_roster                 │
│   Streaming: icu_vitals_stream, claims_stream, pharmacy_inventory_stream   │
└────────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
┌────────────── DATABRICKS SILVER (Unity Catalog + PII Engine) ─────────────┐
│   SCD Type-2  |  Anomaly Detection  |  DQ Gate  |  PII Masking             │
└────────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
┌────────────── DATABRICKS GOLD (KPI Aggregation) ──────────────────────────┐
│   Readmission Rate | Claims Fraud Score | Bed Occupancy | Drug Adherence   │
└────────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
┌────────────── AZURE SYNAPSE ANALYTICS (Dedicated SQL Pool) ───────────────┐
└────────────────────────────────┬──────────────────────────────────────────┘
                                 ▼
              Power BI Dashboards  +  Logic Apps Clinical Alerts
```

---

## 🗂️ Knowledge Base Structure

```text
Hobby_Healthcare_Complex/
├── 00_project_charter/        Project goals, RACI, stakeholders, timeline
├── 01_business_requirements/  BRD v1+v2, FRD, NFR, Use Cases, RTM
├── 02_solution_design/        HLD, LLD, ADRs, Security Design
├── 03_data_dictionary/        Mapping docs, SCD design, incremental strategy
├── 04_onboarding/             New joiner guide, env setup, Azure provisioning
├── 05_data_governance/        PII matrix, DPDP compliance, access control
├── 06_source_data/            7 source folders + schema registry + sample data
├── 07_notebooks/              13 Databricks notebooks (incl. 3 Kafka streaming)
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
├── 20_governance_automation/  PII/PHI scrubbing, maintenance automation
├── 21_kafka_streaming/        [NEW v3.0] Kafka producers, Spark consumers, Avro schemas
│   ├── producers/             ICU vitals + Claims + Pharmacy CDC producers
│   ├── consumers/             Streaming consumer notebook references
│   ├── config/                kafka_config.py, kafka_topics.json
│   ├── schema_registry/       Avro schemas (.avsc)
│   └── docker/                docker-compose.yml (local dev Kafka + ZK + UI)
├── 22_airflow_dags/           [NEW v3.0] Declarative DAG-based pipeline orchestration
│   ├── dags/                  7 Airflow DAGs (bronze, silver, gold, kafka, SLA)
│   ├── plugins/               Custom operators: Databricks, ADF, Kafka sensor
│   └── config/                connections.json, dag_config.yaml, requirements.txt
└── MediFlow360_Interactive_Guide.html  ← INTERACTIVE PLATFORM PORTAL
```

---

## 🚀 Quick Start (Engineering Onboarding)

1. **Access the Portal**: Open `MediFlow360_Interactive_Guide.html` in your browser.
2. **Review the Medallion Implementation**: Read `02_solution_design/LLD_Low_Level_Design.md`.
3. **Start Local Kafka Stack** (streaming dev):
   ```bash
   cd 21_kafka_streaming/docker/
   docker-compose up -d
   # Kafka UI: http://localhost:8080 | Schema Registry: http://localhost:8081
   ```
4. **Run ICU Vitals Simulation**:
   ```bash
   python 21_kafka_streaming/producers/kafka_vitals_producer.py --mode local --rate 5
   ```
5. **Provision Azure Resources**: Use Terraform at `11_infrastructure/terraform/`.

---

## 🔌 Source Systems Integration (7 Types)

| ID | System | Technology | Entity | Integration Pattern |
|----|--------|------------|--------|---------------------|
| S1 | HIS Chennai | MySQL 8.0 (on-prem) | Patients, Admissions | ADF SHIR + Watermark |
| S2 | Insurance | REST API (OAuth2) | Claims, Approvals | **Kafka** `mrhs.insurance.claims` |
| S3 | LIS System | SFTP (CSV) | Lab Results | Blob Event Trigger |
| S4 | Appt. App | CosmosDB (JSON) | Appointments | Watermark Delta |
| S5 | Pharmacy | PostgreSQL 14 | Drug Inventory | **Kafka CDC** `mrhs.pharmacy.cdc` |
| S6 | HR Roster | SharePoint Excel | Staff Roster | Weekly Full Load |
| S7 | ICU Monitors | Azure IoT Hub | ICU Vitals | **Kafka** `mrhs.icu.vitals` |

---

## ⚡ Real-Time Streaming (NEW — v3.0)

| Kafka Topic | Producer | Consumer Notebook | Bronze Table | Watermark |
|-------------|----------|-------------------|--------------|-----------|
| `mrhs.icu.vitals` | `kafka_vitals_producer.py` | `08_Kafka_ICU_Vitals_Stream_NB.py` | `bronze.icu_vitals_stream` | 5 min |
| `mrhs.insurance.claims` | `kafka_claims_producer.py` | `09_Kafka_Claims_Stream_NB.py` | `bronze.claims_stream` | 30 min |
| `mrhs.pharmacy.cdc` | `kafka_pharmacy_cdc_producer.py` | `10_Kafka_Pharmacy_CDC_Stream_NB.py` | `bronze.pharmacy_inventory_stream` | 10 min |

---

## 🌀 Airflow DAG Catalog (NEW — v3.0)

| DAG ID | Schedule (IST) | Description |
|--------|----------------|-------------|
| `bronze_batch_ingestion` | Daily 2:00 AM | S1/S3/S4/S6 batch via ADF, SLA: 3h |
| `silver_transform` | Daily 6:00 AM | SCD2, PII masking, anomaly detection |
| `gold_aggregation` | Daily 9:00 AM | Gold KPIs + Synapse + Power BI refresh |
| `kafka_stream_monitor` | Every 2 min | Consumer lag check + Databricks auto-scale |
| `data_quality_gate` | After bronze DAG | DQ validation gate before Silver promotion |
| `sla_alerting` | Hourly | SLA breach Teams/Email notifications |

---

## 👥 Core Engineering Team

| ID | Name | Role | Focus Area |
|----|------|------|------------|
| SA-001 | Vikram Krishnan | Solution Architect | Synapse, Overall Architecture |
| DE-001 | Priya Sharma | Lead Data Engineer | Databricks, Medallion, Airflow DAGs |
| DE-002 | Arjun Patel | Senior DE | ADF Pipelines, Kafka Producers |
| DE-003 | Kavitha Rajan | Data Engineer | PySpark, Spark Structured Streaming |
| DA-001 | Rahul Nair | Senior Data Analyst | Power BI, Synapse DirectQuery |
| DG-001 | Lakshmi Venkat | Governance Officer | DPDP Compliance, PII Masking |

---

*MediFlow360 v3.0 | MRHS Enterprise Data & Analytics Platform | Highly Confidential*
