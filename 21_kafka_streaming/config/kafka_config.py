"""
MediFlow360 — Shared Kafka / Azure Event Hubs Configuration
Author: Arjun Patel (DE-002) | Version: 2.1 | Last Updated: 2024-05-05
"""

import os
from dataclasses import dataclass
from typing import Dict, Any

def get_secret_val(secret_name: str, default: str = None) -> str:
    """Utility to fetch secrets from environment or conceptual Key Vault."""
    return os.getenv(secret_name.upper().replace("-", "_"), default)

# ─────────────────────────────────────────────────────────────────────────────
# KAFKA TOPIC NAMES & CONSUMER GROUPS
# ─────────────────────────────────────────────────────────────────────────────
class KafkaTopics:
    ICU_VITALS      = "mrhs.icu.vitals"
    CLAIMS          = "mrhs.insurance.claims"
    PHARMACY_CDC    = "mrhs.pharmacy.cdc"
    DLQ             = "mrhs.dlq.all"

class ConsumerGroups:
    VITALS_BRONZE    = "mediflow360-vitals-consumer-grp"
    CLAIMS_BRONZE    = "mediflow360-claims-consumer-grp"
    PHARMACY_CDC     = "mediflow360-pharmacy-cdc-grp"

# ─────────────────────────────────────────────────────────────────────────────
# KAFKA CONNECTION CONFIG
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class KafkaConfig:
    """
    Encapsulates all Kafka / Event Hubs connection parameters.
    Integrates with Azure Key Vault via get_secret_val().
    """
    bootstrap_servers: str = get_secret_val("kafka-bootstrap-servers", "localhost:9092")
    security_protocol: str = get_secret_val("kafka-security-protocol", "SASL_SSL")
    sasl_mechanism: str    = get_secret_val("kafka-sasl-mechanism", "PLAIN")
    username: str          = get_secret_val("kafka-username", "$ConnectionString")
    password: str          = get_secret_val("kafka-password") # SAS token or Service Principal
    client_id: str         = "mediflow360-client-01"

    def get_producer_config(self) -> Dict[str, Any]:
        """Returns configuration dictionary for confluent_kafka.Producer"""
        config = {
            'bootstrap.servers':  self.bootstrap_servers,
            'client.id':          self.client_id,
            'acks':               'all',
            'retries':            5,
            'linger.ms':          5,
        }
        
        if self.security_protocol != "PLAINTEXT":
            config.update({
                'security.protocol': self.security_protocol,
                'sasl.mechanisms':   self.sasl_mechanism,
                'sasl.username':     self.username,
                'sasl.password':     self.password,
            })
        return config

    def get_spark_options(self, topic: str, group_id: str) -> Dict[str, str]:
        """Returns options for spark.readStream.format('kafka')"""
        options = {
            "kafka.bootstrap.servers": self.bootstrap_servers,
            "subscribe":               topic,
            "kafka.group.id":          group_id,
            "startingOffsets":         "latest",
            "failOnDataLoss":          "false"
        }
        
        if self.security_protocol != "PLAINTEXT":
            jaas_config = (
                f"kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required "
                f"username=\"{self.username}\" "
                f"password=\"{self.password}\";"
            )
            options.update({
                "kafka.security.protocol": self.security_protocol,
                "kafka.sasl.mechanism":    self.sasl_mechanism,
                "kafka.sasl.jaas.config":  jaas_config
            })
        return options

# ─────────────────────────────────────────────────────────────────────────────
# CHECKPOINT PATHS & THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────
CHECKPOINT_BASE = "abfss://mediflow360@mrhsadlsprod.dfs.core.windows.net/streaming/checkpoints"

LAG_THRESHOLDS = {
    KafkaTopics.ICU_VITALS:    500,
    KafkaTopics.CLAIMS:        200,
    KafkaTopics.PHARMACY_CDC:  100,
}

# Instance for shared use
mediflow_kafka_config = KafkaConfig()
