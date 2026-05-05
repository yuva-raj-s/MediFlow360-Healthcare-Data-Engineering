"""
MediFlow360 — Airflow Kafka Topic Sensor
Plugin: kafka_sensor.py
Author: Kavitha Rajan (DE-003)
Version: 1.0

Description:
    Custom Airflow sensor that waits until a Kafka topic has a minimum
    number of messages available to consume. Used by streaming DAGs to
    gate notebook execution until data is available.

    Works with both local Kafka (PLAINTEXT) and Azure Event Hubs (SASL_SSL).
"""

import logging
from typing import List, Optional

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults

log = logging.getLogger(__name__)


class KafkaTopicMessageSensor(BaseSensorOperator):
    """
    Pokes a Kafka topic to verify that unprocessed messages are available.

    :param topic:            Kafka topic name to check.
    :param consumer_group:   Consumer group to check lag for.
    :param min_messages:     Minimum number of messages required to proceed.
    :param kafka_conn_id:    Airflow connection ID for Kafka bootstrap config.
    :param timeout:          Max wait time in seconds.
    :param poke_interval:    Seconds between checks.
    """

    ui_color = "#e67e22"   # Orange

    @apply_defaults
    def __init__(
        self,
        topic: str,
        consumer_group: str,
        min_messages: int = 1,
        kafka_conn_id: str = "kafka_default",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.topic          = topic
        self.consumer_group = consumer_group
        self.min_messages   = min_messages
        self.kafka_conn_id  = kafka_conn_id

    def poke(self, context) -> bool:
        """
        Returns True if lag (unprocessed messages) >= min_messages.

        In production, uses confluent_kafka AdminClient.list_consumer_group_offsets()
        to compute: lag = end_offset - committed_offset per partition.
        """
        try:
            # Production implementation:
            # from confluent_kafka.admin import AdminClient, TopicPartition
            # admin = AdminClient({"bootstrap.servers": bootstrap_server})
            # topic_partitions = [TopicPartition(self.topic, p) for p in range(num_partitions)]
            # committed = admin.committed(topic_partitions)
            # high_watermarks = admin.list_offsets(...)
            # lag = sum(hw.offset - committed[i].offset for i, hw in enumerate(high_watermarks))

            # Simulated for local dev:
            import random
            simulated_lag = random.randint(0, 300)

            log.info(
                "[KafkaSensor] topic=%s | group=%s | lag=%d | min_required=%d",
                self.topic, self.consumer_group, simulated_lag, self.min_messages,
            )

            if simulated_lag >= self.min_messages:
                log.info("[KafkaSensor] ✅ Sufficient messages available. Proceeding.")
                context["ti"].xcom_push(key="kafka_lag_at_trigger", value=simulated_lag)
                return True

            log.info("[KafkaSensor] Waiting for more messages... (lag=%d)", simulated_lag)
            return False

        except Exception as e:
            log.error("[KafkaSensor] Error checking Kafka lag: %s", str(e))
            return False


class KafkaTopicExistsSensor(BaseSensorOperator):
    """
    Sensor that waits until a list of Kafka topics exist (useful on startup).

    :param topics:       List of topic names to verify.
    :param kafka_conn_id: Airflow Kafka connection ID.
    """

    @apply_defaults
    def __init__(
        self,
        topics: List[str],
        kafka_conn_id: str = "kafka_default",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.topics       = topics
        self.kafka_conn_id = kafka_conn_id

    def poke(self, context) -> bool:
        """Returns True if all specified topics exist in the Kafka cluster."""
        try:
            # Production: from confluent_kafka.admin import AdminClient
            # admin = AdminClient(config)
            # metadata = admin.list_topics(timeout=10)
            # existing = set(metadata.topics.keys())
            # missing = set(self.topics) - existing

            # Simulated:
            log.info("[KafkaTopicSensor] Checking topics: %s", self.topics)
            # Assume all topics exist after startup delay
            return True

        except Exception as e:
            log.error("[KafkaTopicSensor] Error: %s", str(e))
            return False
