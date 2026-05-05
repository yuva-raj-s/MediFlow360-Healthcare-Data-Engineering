"""
MediFlow360 — Shared Kafka / Azure Event Hubs Configuration
Used by: Kafka producers, Spark Structured Streaming consumers, Airflow operators
Author: Arjun Patel (DE-002)
Version: 1.0
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict


# ─────────────────────────────────────────────────────────────────────────────
# KAFKA TOPIC NAMES (single source of truth)
# ─────────────────────────────────────────────────────────────────────────────
class KafkaTopics:
    ICU_VITALS      = "mrhs.icu.vitals"
    CLAIMS          = "mrhs.insurance.claims"
    PHARMACY_CDC    = "mrhs.pharmacy.cdc"
    PATIENT_EVENTS  = "mrhs.patients.events"    # Future: patient admission/discharge
    LAB_RESULTS     = "mrhs.lab.results"        # Future: real-time lab result stream
    DLQ             = "mrhs.dlq.all"            # Dead Letter Queue (unified)

    ALL_TOPICS = [ICU_VITALS, CLAIMS, PHARMACY_CDC]


# ─────────────────────────────────────────────────────────────────────────────
# CONSUMER GROUPS
# ─────────────────────────────────────────────────────────────────────────────
class ConsumerGroups:
    VITALS_BRONZE    = "mediflow360-vitals-consumer-grp"
    CLAIMS_BRONZE    = "mediflow360-claims-consumer-grp"
    PHARMACY_CDC     = "mediflow360-pharmacy-cdc-grp"
    DQ_MONITOR       = "mediflow360-dq-monitor-grp"
    AIRFLOW_LAG_CHK  = "mediflow360-airflow-lag-grp"


# ─────────────────────────────────────────────────────────────────────────────
# KAFKA CONNECTION CONFIG
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class KafkaConfig:
    """
    Encapsulates all Kafka / Event Hubs connection parameters.
    In production, secrets are loaded from Azure Key Vault.
    In local dev, they are loaded from environment variables.
    """
    bootstrap_servers: str
    use_sasl: bool          = False
    sasl_username: str      = ""
    sasl_password: str      = ""
    security_protocol: str  = "PLAINTEXT"
    sasl_mechanism: str     = "PLAIN"
    schema_registry_url: str = ""

    @classmethod
    def local(cls) -> "KafkaConfig":
        """Local Docker Kafka configuration."""
        return cls(
            bootstrap_servers   = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
            schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
        )

    @classmethod
    def azure_event_hubs(cls, namespace: str, connection_string: str) -> "KafkaConfig":
        """Azure Event Hubs Kafka-compatible endpoint configuration."""
        return cls(
            bootstrap_servers   = f"{namespace}.servicebus.windows.net:9093",
            use_sasl            = True,
            sasl_username       = "$ConnectionString",
            sasl_password       = connection_string,
            security_protocol   = "SASL_SSL",
            sasl_mechanism      = "PLAIN",
            schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", ""),
        )

    def to_producer_config(self) -> dict:
        """Convert to kafka-python KafkaProducer kwargs."""
        cfg = {
            "bootstrap_servers":   self.bootstrap_servers,
            "acks":                "all",
            "retries":             5,
            "retry_backoff_ms":    300,
            "compression_type":    "gzip",
            "linger_ms":           10,
        }
        if self.use_sasl:
            cfg.update({
                "security_protocol":   self.security_protocol,
                "sasl_mechanism":      self.sasl_mechanism,
                "sasl_plain_username": self.sasl_username,
                "sasl_plain_password": self.sasl_password,
            })
        return cfg

    def to_spark_readstream_options(self, topic: str, group_id: str, starting_offsets: str = "latest") -> dict:
        """Convert to Spark Structured Streaming readStream options."""
        opts = {
            "kafka.bootstrap.servers": self.bootstrap_servers,
            "subscribe":               topic,
            "startingOffsets":         starting_offsets,
            "failOnDataLoss":          "false",
            "kafka.group.id":          group_id,
        }
        if self.use_sasl:
            jaas = (
                f"kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required "
                f"username=\"{self.sasl_username}\" "
                f"password=\"{self.sasl_password}\";"
            )
            opts.update({
                "kafka.security.protocol":  self.security_protocol,
                "kafka.sasl.mechanism":     self.sasl_mechanism,
                "kafka.sasl.jaas.config":   jaas,
            })
        return opts


# ─────────────────────────────────────────────────────────────────────────────
# CONSUMER LAG THRESHOLDS (for Airflow monitoring)
# ─────────────────────────────────────────────────────────────────────────────
LAG_THRESHOLDS = {
    KafkaTopics.ICU_VITALS:    500,     # Max 500 unprocessed vital records
    KafkaTopics.CLAIMS:        200,     # Max 200 unprocessed claim events
    KafkaTopics.PHARMACY_CDC:  100,     # Max 100 unprocessed CDC events
}

# ─────────────────────────────────────────────────────────────────────────────
# CHECKPOINT PATHS (ADLS Gen2)
# ─────────────────────────────────────────────────────────────────────────────
CHECKPOINT_BASE = "abfss://mediflow360@mrhsadlsprod.dfs.core.windows.net/streaming/checkpoints"

CHECKPOINTS = {
    KafkaTopics.ICU_VITALS:    f"{CHECKPOINT_BASE}/vitals",
    KafkaTopics.CLAIMS:        f"{CHECKPOINT_BASE}/claims",
    KafkaTopics.PHARMACY_CDC:  f"{CHECKPOINT_BASE}/pharmacy_cdc",
}
