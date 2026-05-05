"""
MediFlow360 — Kafka ICU Vitals Producer (v2.1)
Author: Arjun Patel (DE-002) | Version: 2.1 | Last Updated: 2024-05-05
"""

import json
import time
import random
import logging
from datetime import datetime, timezone
from confluent_kafka import Producer
from config.kafka_config import mediflow_kafka_config, KafkaTopics

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
log = logging.getLogger("ICUProducer")

class ICUProducer:
    def __init__(self, config=mediflow_kafka_config):
        self.config = config
        self.producer = Producer(self.config.get_producer_config())
        self.topic = KafkaTopics.ICU_VITALS

    def delivery_report(self, err, msg):
        """Callback for async delivery reports."""
        if err is not None:
            log.error(f"❌ Message delivery FAILED: {err}")
        else:
            log.info(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

    def generate_vital_signs(self, device_id: str, patient_mrn: str, hospital_code: str, anomaly_rate: float = 0.05) -> dict:
        """Simulates an ICU vital sign reading."""
        is_anomaly = random.random() < anomaly_rate
        
        heart_rate = random.randint(60, 100) if not is_anomaly else random.choice([40, 140])
        spo2 = round(random.uniform(95.0, 99.9), 1) if not is_anomaly else 88.5
        
        return {
            "device_id": device_id,
            "patient_mrn": patient_mrn,
            "hospital_code": hospital_code,
            "heart_rate": heart_rate,
            "spo2": spo2,
            "systolic_bp": random.randint(110, 130),
            "diastolic_bp": random.randint(70, 85),
            "temperature_c": round(random.uniform(36.5, 37.5), 1),
            "alert_level": "CRITICAL" if is_anomaly else "NORMAL",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

    def start_simulation(self, rate: int = 1):
        """Starts the production loop."""
        log.info(f"🚀 Starting ICU Vitals Stream to {self.topic}...")
        try:
            while True:
                data = self.generate_vital_signs("ICU-BED-01", "PAT-999", "CHN")
                self.producer.produce(
                    self.topic, 
                    key=data["device_id"], 
                    value=json.dumps(data), 
                    callback=self.delivery_report
                )
                self.producer.poll(0)
                time.sleep(1.0 / rate)
        except KeyboardInterrupt:
            log.info("🛑 Stream stopped by user.")
        finally:
            self.producer.flush()

if __name__ == "__main__":
    p = ICUProducer()
    p.start_simulation(rate=5)

