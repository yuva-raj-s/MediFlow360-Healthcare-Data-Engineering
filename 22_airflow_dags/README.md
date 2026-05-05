# 22 — Apache Airflow Orchestration Layer
## MediFlow360 | Declarative DAG-Based Pipeline Orchestration

---

## Overview

This folder implements the **Apache Airflow orchestration layer** for MediFlow360, replacing manual ADF schedule dependencies with fully-declarative, SLA-aware, dependency-tracked DAGs. Airflow orchestrates both batch (ADF-based) and real-time (Kafka/Spark Structured Streaming) pipelines from a single pane of glass.

---

## Deployment Options

| Option | Description | Recommended For |
|--------|-------------|-----------------|
| **MWAA** | AWS Managed Airflow | Azure-to-AWS hybrid |
| **Astronomer** | Cloud-managed Airflow on AKS | Enterprise (MRHS recommended) |
| **Docker Compose** | Local developer environment | Dev/testing only |

**MRHS uses Astronomer on AKS** (Azure Kubernetes Service) in the `southindia` region.

---

## DAG Catalog

| DAG ID | Schedule | Description | SLA |
|--------|----------|-------------|-----|
| `mediflow360_master` | Manual / Webhook | Master orchestrator, triggers all child DAGs | N/A |
| `bronze_batch_ingestion` | `0 2 * * *` (2am IST) | S1 MySQL, S3 SFTP, S4 CosmosDB, S6 SharePoint | 3h |
| `silver_transform` | `0 6 * * *` (6am IST) | Silver layer: SCD2, PII masking, quality gates | 2h |
| `gold_aggregation` | `0 9 * * *` (9am IST) | Gold KPIs + Synapse sync | 1h |
| `kafka_stream_monitor` | `*/2 * * * *` (every 2min) | Consumer lag check + auto-scale trigger | 2min |
| `data_quality_gate` | After silver_transform | DQ validation before Silver promotion | 30min |
| `sla_alerting` | `0 * * * *` (hourly) | SLA breach detection + Teams/Email alert | 10min |

---

## Folder Structure

```text
22_airflow_dags/
├── README.md                          ← This file
├── dags/
│   ├── dag_mediflow360_master.py      ← Master orchestrator DAG
│   ├── dag_bronze_batch_ingestion.py  ← Batch ingestion DAG
│   ├── dag_silver_transform.py        ← Silver transformation DAG
│   ├── dag_gold_aggregation.py        ← Gold aggregation DAG
│   ├── dag_kafka_stream_monitor.py    ← Kafka consumer lag monitor
│   ├── dag_data_quality_gate.py       ← DQ gate (runs after silver)
│   └── dag_sla_alerting.py            ← SLA breach detection DAG
├── plugins/
│   ├── databricks_operator.py         ← Custom: runs Databricks notebook/job
│   ├── adf_operator.py                ← Custom: triggers ADF pipeline run
│   ├── kafka_sensor.py                ← Custom: waits for Kafka topic messages
│   └── mediflow_hooks.py              ← Shared hooks (Databricks, ADF, Monitor)
└── config/
    ├── airflow_connections.json       ← Airflow connection definitions
    ├── dag_config.yaml                ← Schedule, retry, SLA per DAG
    └── requirements.txt               ← Airflow provider packages
```

---

## Airflow Connections Required

Configure these in Airflow > Admin > Connections:

| Connection ID | Type | Description |
|---------------|------|-------------|
| `databricks_default` | HTTP | Databricks workspace URL + PAT token |
| `azure_data_factory` | HTTP | ADF management API + Service Principal |
| `azure_sql_mediflow` | MSSQL | Azure SQL metadata/watermark DB |
| `teams_webhook`       | HTTP | Teams webhook for alert delivery |
| `kafka_default`       | Kafka | Event Hubs bootstrap + SASL creds |

---

## Environment Variables (Airflow)

Set via Astronomer Secrets or Kubernetes Secrets:

```bash
AIRFLOW__CORE__FERNET_KEY=<base64-encoded-32-byte-key>
DATABRICKS_HOST=https://adb-XXXXXXXX.azuredatabricks.net
DATABRICKS_TOKEN=<pat-token>
ADF_SUBSCRIPTION_ID=<azure-subscription-id>
ADF_RESOURCE_GROUP=mrhs-rg-prod
ADF_FACTORY_NAME=mrhs-adf-prod
```

---

## SLA Monitoring

Airflow SLA misses are captured in the `sla_miss` callback in each DAG and:
1. Send a Teams card via `send_teams_alert()`
2. Create an incident ticket in `15_incidents_and_struggles/`
3. Log to Azure Monitor custom metrics

---

*MediFlow360 v3.0 | Airflow Orchestration Layer | MRHS Data Engineering Team*
