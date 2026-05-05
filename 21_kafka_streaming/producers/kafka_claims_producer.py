"""
MediFlow360 — Kafka Claims API Producer (v2.1)
Author: Arjun Patel (DE-002) | Version: 2.1 | Last Updated: 2024-05-05
"""

import json
import time
import random
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from confluent_kafka import Producer
from config.kafka_config import mediflow_kafka_config, KafkaTopics

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
log = logging.getLogger("ClaimsProducer")

OFFSET_FILE = Path(__file__).parent / ".claims_producer_offset.json"

class ClaimsProducer:
    def __init__(self, config=mediflow_kafka_config):
        self.config = config
        self.producer = Producer(self.config.get_producer_config())
        self.topic = KafkaTopics.CLAIMS

    def delivery_report(self, err, msg):
        if err is not None:
            log.error(f"❌ Message delivery FAILED: {err}")
        else:
            log.info(f"✅ Claim {msg.key().decode('utf-8')} delivered to {msg.topic()}")

    def load_offset(self) -> int:
        if OFFSET_FILE.exists():
            with open(OFFSET_FILE) as f:
                return json.load(f).get("last_claim_id", 0)
        return 0

    def save_offset(self, last_id: int):
        with open(OFFSET_FILE, "w") as f:
            json.dump({"last_claim_id": last_id, "last_poll_at": datetime.now(timezone.utc).isoformat()}, f)

    def simulate_api_poll(self, last_id: int) -> list:
        """Simulates insurance API polling."""
        new_claims = []
        count = random.randint(0, 5)
        for i in range(count):
            cid = last_id + i + 1
            new_claims.append({
                "claim_id": f"CLM-{str(cid).zfill(8)}",
                "hospital_code": random.choice(["CHN", "MDU", "CBE"]),
                "amount": round(random.uniform(1000, 50000), 2),
                "status": "PENDING",
                "submitted_at": datetime.now(timezone.utc).isoformat()
            })
        return new_claims

    def start_polling(self, interval: int = 30):
        log.info(f"🚀 Starting Claims API Poller to {self.topic}...")
        last_id = self.load_offset()
        try:
            while True:
                claims = self.simulate_api_poll(last_id)
                if claims:
                    for c in claims:
                        self.producer.produce(
                            self.topic, 
                            key=c["claim_id"], 
                            value=json.dumps(c), 
                            callback=self.delivery_report
                        )
                    self.producer.flush()
                    last_id += len(claims)
                    self.save_offset(last_id)
                else:
                    log.info("💤 No new claims. Sleeping...")
                time.sleep(interval)
        except KeyboardInterrupt:
            log.info("🛑 Poller stopped.")
        finally:
            self.producer.flush()

if __name__ == "__main__":
    p = ClaimsProducer()
    p.start_polling(interval=10)

