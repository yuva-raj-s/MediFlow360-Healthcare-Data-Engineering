# 21 — Kafka Real-Time Streaming Layer
## MediFlow360 | Real-Time Event Streaming Architecture

---

## Overview

This folder implements the **real-time streaming ingestion layer** for MediFlow360, built on **Apache Kafka** (via Azure Event Hubs Kafka-compatible endpoint). It complements the existing batch ADF pipelines by enabling sub-second data ingestion from IoT devices, insurance claim APIs, and pharmacy CDC streams.

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                  REAL-TIME STREAMING LAYER (Kafka)                   │
│                                                                      │
│  ICU Monitors (IoT Hub)  ──→  Kafka Topic: mrhs.icu.vitals          │
│  Insurance Claims API    ──→  Kafka Topic: mrhs.insurance.claims    │
│  Pharmacy CDC (Debezium) ──→  Kafka Topic: mrhs.pharmacy.cdc        │
│                                    │                                 │
│                        Azure Event Hubs (Kafka-compatible)           │
│                                    │                                 │
│              Spark Structured Streaming (Databricks)                 │
│                                    │                                 │
│         Bronze Delta Tables (ADLS Gen2 → Unity Catalog)             │
│  ├── mediflow_prod.bronze.icu_vitals_stream                          │
│  ├── mediflow_prod.bronze.claims_stream                              │
│  └── mediflow_prod.bronze.pharmacy_cdc_stream                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```text
21_kafka_streaming/
├── README.md                          ← This file
├── producers/
│   ├── kafka_vitals_producer.py       ← ICU monitor simulator → Kafka
│   ├── kafka_claims_producer.py       ← Claims API poller → Kafka
│   └── kafka_pharmacy_cdc_producer.py ← PostgreSQL CDC → Kafka
├── consumers/
│   ├── 08_Kafka_ICU_Vitals_Stream_NB.py   ← Spark Structured Streaming → Bronze
│   ├── 09_Kafka_Claims_Stream_NB.py       ← Claims streaming → Bronze
│   └── 10_Kafka_Pharmacy_CDC_Stream_NB.py ← CDC MERGE → Bronze
├── config/
│   ├── kafka_config.py            ← Shared Kafka connection config
│   ├── kafka_topics.json          ← Topic definitions & retention
│   └── event_hubs_config.json     ← Azure Event Hubs Kafka endpoint
├── schema_registry/
│   ├── vitals_schema.avsc         ← Avro schema: ICU vitals
│   ├── claims_schema.avsc         ← Avro schema: Claims
│   └── pharmacy_cdc_schema.avsc   ← Avro schema: CDC events
└── docker/
    ├── docker-compose.yml         ← Local dev: Kafka + ZK + Schema Registry
    └── Dockerfile.producer        ← Producer containerization
```

---

## Kafka Topics (Azure Event Hubs)

| Topic Name                | Source System    | Partitions | Retention | Avro Schema          |
|---------------------------|------------------|------------|-----------|----------------------|
| `mrhs.icu.vitals`         | ICU Monitors (S7)| 12         | 7 days    | `vitals_schema.avsc` |
| `mrhs.insurance.claims`   | Claims API (S2)  | 6          | 14 days   | `claims_schema.avsc` |
| `mrhs.pharmacy.cdc`       | PostgreSQL (S5)  | 4          | 3 days    | `pharmacy_cdc_schema.avsc` |

---

## Streaming Checkpointing

All Spark Structured Streaming jobs use **ADLS Gen2 checkpointing** to ensure exactly-once semantics:

```
abfss://mediflow360@mrhsadlsprod.dfs.core.windows.net/streaming/checkpoints/
├── vitals/
├── claims/
└── pharmacy_cdc/
```

---

## Late Data Handling

| Stream          | Watermark | Out-of-Order Tolerance |
|-----------------|-----------|------------------------|
| ICU Vitals      | 5 minutes | High-frequency data    |
| Claims          | 30 minutes| API pagination delays  |
| Pharmacy CDC    | 10 minutes| WAL replication lag    |

---

## Consumer Lag Monitoring

The **Airflow DAG** `dag_kafka_stream_monitor.py` (in `22_airflow_dags/`) monitors consumer lag every 2 minutes via the Confluent Schema Registry API and triggers Teams alerts if lag exceeds configured thresholds.

---

## Local Development

Run the full local Kafka stack:

```bash
cd 21_kafka_streaming/docker/
docker-compose up -d

# Verify topics are created
docker exec -it kafka kafka-topics.sh --bootstrap-server localhost:9092 --list

# Start a producer (ICU vitals simulation)
python producers/kafka_vitals_producer.py --mode local --rate 10
```

---

*MediFlow360 v3.0 | Kafka Streaming Layer | MRHS Data Engineering Team*
