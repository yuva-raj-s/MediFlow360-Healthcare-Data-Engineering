# test_kafka_pipelines.py — Unit Tests for Streaming Components
# Author: Rahul Nair (DE-001) | Version: 1.0 | Date: 2024-05-05

import unittest
from unittest.mock import MagicMock, patch
import json

# Add project root to sys.path if necessary
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '21_kafka_streaming')))

from producers.kafka_vitals_producer import ICUProducer
from config.kafka_config import KafkaConfig

class TestKafkaProducers(unittest.TestCase):

    def setUp(self):
        self.mock_conf = KafkaConfig(bootstrap_servers="localhost:9092", security_protocol="PLAINTEXT")
        self.producer = ICUProducer(self.mock_conf)

    @patch('confluent_kafka.Producer')
    def test_vital_message_generation(self, mock_producer_class):
        """Test if vital signs are generated within logical clinical ranges."""
        vital_data = self.producer.generate_vital_signs("DEVICE-001", "MRN-123", "HOSP-A")
        
        self.assertEqual(vital_data['device_id'], "DEVICE-001")
        self.assertIn(vital_data['alert_level'], ["NORMAL", "WARNING", "CRITICAL"])
        self.assertGreater(vital_data['heart_rate'], 20)
        self.assertLess(vital_data['heart_rate'], 300)

    @patch('confluent_kafka.Producer')
    def test_producer_delivery_callback(self, mock_producer_class):
        """Test the Kafka delivery report callback logic."""
        mock_err = MagicMock()
        mock_err.return_value = None # No error
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 0
        mock_msg.offset.return_value = 101

        # We simulate the callback directly
        with self.assertLogs(level='INFO') as cm:
            self.producer.delivery_report(None, mock_msg)
            self.assertTrue(any("Message delivered to test-topic" in line for line in cm.output))

class TestStreamingLogic(unittest.TestCase):
    """
    Conceptual tests for Spark Streaming logic.
    In a real CI/CD, these would use a local SparkSession with MemoryStream.
    """
    
    def test_schema_parsing(self):
        # This would test VITALS_SCHEMA from the notebook
        pass

if __name__ == '__main__':
    unittest.main()
