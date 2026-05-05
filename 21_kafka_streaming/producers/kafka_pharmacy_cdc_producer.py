"""
MediFlow360 — Kafka Pharmacy CDC Producer (v2.1)
Author: Kavitha Rajan (DE-003) | Version: 2.1 | Last Updated: 2024-05-05
"""

import json
import time
import random
import logging
from datetime import datetime, timezone, timedelta
from confluent_kafka import Producer
from config.kafka_config import mediflow_kafka_config, KafkaTopics

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
log = logging.getLogger("PharmacyCDCProducer")

class PharmacyCDCProducer:
    def __init__(self, config=mediflow_kafka_config):
        self.config = config
        self.producer = Producer(self.config.get_producer_config())
        self.topic = KafkaTopics.PHARMACY_CDC

    def delivery_report(self, err, msg):
        if err is not None:
            log.error(f"❌ CDC Event delivery FAILED: {err}")
        else:
            log.info(f"✅ CDC Event {msg.key().decode('utf-8')} delivered to {msg.topic()}")

    def build_cdc_envelope(self, op: str, table: str, after: dict) -> dict:
        """Constructs a Debezium-like CDC envelope."""
        return {
            "op": op,
            "ts_ms": int(datetime.now(timezone.utc).timestamp() * 1000),
            "after": after,
            "source": {
                "table": table,
                "db": "pharmacy_db",
                "lsn": random.randint(1000, 9999)
            }
        }

    def generate_inventory_event(self) -> dict:
        """Simulates an inventory update."""
        item_id = f"ITEM-{random.randint(100, 999)}"
        data = {
            "item_id": item_id,
            "hospital_code": random.choice(["CHN", "MDU"]),
            "stock_count": random.randint(10, 500),
            "reorder_level": 50,
            "last_updated_at": datetime.now(timezone.utc).isoformat()
        }
        return self.build_cdc_envelope("u", "drug_inventory", data)

    def start_simulation(self, rate: int = 1):
        log.info(f"🚀 Starting Pharmacy CDC Stream to {self.topic}...")
        try:
            while True:
                event = self.generate_inventory_event()
                key = event["after"]["item_id"]
                self.producer.produce(
                    self.topic, 
                    key=key, 
                    value=json.dumps(event), 
                    callback=self.delivery_report
                )
                self.producer.poll(0)
                time.sleep(1.0 / rate)
        except KeyboardInterrupt:
            log.info("🛑 Stream stopped.")
        finally:
            self.producer.flush()

if __name__ == "__main__":
    p = PharmacyCDCProducer()
    p.start_simulation(rate=2)

