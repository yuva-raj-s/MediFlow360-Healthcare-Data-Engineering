"""
MediFlow360 — Kafka Claims API Producer
Source: S2 Insurance Claims REST API → Kafka Topic: mrhs.insurance.claims
Author: Arjun Patel (DE-002)
Version: 1.0 | Date: 2024-04-02

Description:
    Polls the insurance claims REST API (paginated, OAuth2) and publishes
    new/updated claim records to the Kafka topic mrhs.insurance.claims.
    Uses a file-based offset file to track last processed claim ID and
    ensure no duplicates across restarts (idempotent producer pattern).

    Claim Event Model:
        event_type     : str  — "claim_created" | "claim_updated" | "claim_approved" | "claim_denied"
        claim_id       : str  — Unique claim identifier from insurance system
        patient_mrn    : str  — MRN cross-reference
        hospital_code  : str  — CHN | MDU | CBE | TRV
        claim_amount   : float — INR amount billed
        approved_amount: float — INR amount approved (null if pending)
        status         : str  — PENDING | APPROVED | DENIED | PARTIAL
        service_date   : str  — ISO date of medical service
        submitted_at   : str  — ISO timestamp
        processed_at   : str  — ISO timestamp (null if pending)
        icd_codes      : list — ICD-10 diagnosis codes
        procedure_codes: list — CPT/procedure codes
"""

import os
import json
import time
import random
import logging
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("KafkaClaimsProducer")

# ── Constants ──────────────────────────────────────────────────────────────────
TOPIC_CLAIMS        = "mrhs.insurance.claims"
OFFSET_FILE         = Path(__file__).parent / ".claims_producer_offset.json"
POLL_INTERVAL_SEC   = 30          # Poll API every 30 seconds
API_PAGE_SIZE       = 100         # Records per API page
HOSPITALS           = ["CHN", "MDU", "CBE", "TRV"]

# Simulated ICD-10 codes used in MRHS (cardiology, diabetology, nephrology)
ICD10_POOL = [
    "I21.0",  # STEMI anterior wall
    "E11.9",  # Type 2 diabetes mellitus
    "N18.3",  # CKD stage 3
    "J18.9",  # Pneumonia, unspecified
    "I50.9",  # Heart failure, unspecified
    "K92.1",  # Melena
    "I63.9",  # Cerebral infarction
    "A09",    # Gastroenteritis
]

CPT_POOL = [
    "99213",  # Office visit, est. patient
    "93000",  # ECG routine
    "71046",  # Chest X-ray 2 views
    "83036",  # HbA1c test
    "90837",  # Psychotherapy 60min
    "27447",  # Total knee arthroplasty
    "47562",  # Laparoscopic cholecystectomy
]

CLAIM_STATUSES = ["PENDING", "APPROVED", "DENIED", "PARTIAL"]
CLAIM_EVENT_TYPES = {
    "PENDING":  "claim_created",
    "APPROVED": "claim_approved",
    "DENIED":   "claim_denied",
    "PARTIAL":  "claim_updated",
}


def load_offset() -> dict:
    """Load last processed offset from disk."""
    if OFFSET_FILE.exists():
        with open(OFFSET_FILE) as f:
            return json.load(f)
    return {"last_claim_id": 0, "last_poll_at": None}


def save_offset(offset: dict):
    """Persist offset to disk for restart safety."""
    with open(OFFSET_FILE, "w") as f:
        json.dump(offset, f, indent=2)


def simulate_api_poll(last_claim_id: int, page_size: int = 100) -> list:
    """
    Simulate paginated insurance API response.
    In production, replace with:
        GET /api/v3/claims?since_id={last_claim_id}&page_size={page_size}
        Authorization: Bearer {oauth2_token}
    """
    new_claims = []
    num_new = random.randint(0, min(page_size, 15))  # 0–15 new claims per poll

    for i in range(num_new):
        claim_id    = f"CLM-{str(last_claim_id + i + 1).zfill(8)}"
        hospital    = random.choice(HOSPITALS)
        status      = random.choices(CLAIM_STATUSES, weights=[40, 35, 15, 10])[0]
        amount      = round(random.uniform(5000, 250000), 2)
        approved    = None
        if status in ("APPROVED", "PARTIAL"):
            approved = round(amount * random.uniform(0.6, 1.0), 2)

        service_date  = (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).date().isoformat()
        submitted_at  = datetime.now(timezone.utc).isoformat()
        processed_at  = datetime.now(timezone.utc).isoformat() if status != "PENDING" else None

        claim = {
            "event_type":      CLAIM_EVENT_TYPES[status],
            "schema_version":  "2.0",
            "claim_id":        claim_id,
            "patient_mrn":     f"MRN-{hospital}-{str(random.randint(1, 9999)).zfill(5)}",
            "hospital_code":   hospital,
            "insurer_code":    random.choice(["TATA-AIG", "STAR-HEALTH", "NIVA-BUPA", "HDFC-ERGO"]),
            "claim_amount":    amount,
            "approved_amount": approved,
            "status":          status,
            "service_date":    service_date,
            "submitted_at":    submitted_at,
            "processed_at":    processed_at,
            "icd_codes":       random.sample(ICD10_POOL, k=random.randint(1, 3)),
            "procedure_codes": random.sample(CPT_POOL, k=random.randint(1, 2)),
            "is_inpatient":    random.choice([True, False]),
            "ingestion_source": "CLAIMS_API_POLLER_v2.0",
        }
        new_claims.append(claim)

    return new_claims


def get_kafka_producer(bootstrap_servers: str, use_sasl: bool = False, sasl_config: dict = None) -> KafkaProducer:
    """Create KafkaProducer with JSON serialization and idempotent delivery."""
    config = {
        "bootstrap_servers":   bootstrap_servers,
        "value_serializer":    lambda v: json.dumps(v).encode("utf-8"),
        "key_serializer":      lambda k: k.encode("utf-8") if k else None,
        "acks":                "all",
        "retries":             10,
        "retry_backoff_ms":    500,
        "enable_idempotence":  True,    # Exactly-once producer semantics
        "max_in_flight_requests_per_connection": 5,
        "compression_type":    "gzip",
    }

    if use_sasl and sasl_config:
        config.update({
            "security_protocol":   "SASL_SSL",
            "sasl_mechanism":      "PLAIN",
            "sasl_plain_username": sasl_config["username"],
            "sasl_plain_password": sasl_config["password"],
        })

    return KafkaProducer(**config)


def run_claims_producer(
    bootstrap_servers: str,
    poll_interval: int = POLL_INTERVAL_SEC,
    use_sasl: bool = False,
    sasl_config: dict = None,
    run_duration_seconds: int = None,
):
    """
    Main polling loop: simulate API → Kafka.
    Uses file-based offset to resume across restarts.
    """
    producer = get_kafka_producer(bootstrap_servers, use_sasl, sasl_config)
    offset   = load_offset()
    last_id  = offset.get("last_claim_id", 0)

    log.info("🚀 Claims Producer started | Topic: %s | Poll interval: %ds | Last claim ID: %d",
              TOPIC_CLAIMS, poll_interval, last_id)

    total_sent = 0
    start_time = time.time()

    try:
        while True:
            claims = simulate_api_poll(last_id, API_PAGE_SIZE)

            if claims:
                log.info("📡 Fetched %d new claims since claim_id %d", len(claims), last_id)

                for claim in claims:
                    try:
                        producer.send(
                            topic=TOPIC_CLAIMS,
                            key=claim["claim_id"],
                            value=claim,
                        )
                        total_sent += 1
                    except KafkaError as ke:
                        log.error("❌ Failed to send claim %s: %s", claim["claim_id"], ke)

                producer.flush()
                # Update offset to highest claim ID sent
                new_last_id = last_id + len(claims)
                save_offset({"last_claim_id": new_last_id, "last_poll_at": datetime.now(timezone.utc).isoformat()})
                last_id = new_last_id
                log.info("✅ Sent %d claims | New offset: %d | Total sent: %d", len(claims), last_id, total_sent)
            else:
                log.info("💤 No new claims since last poll. Sleeping %ds...", poll_interval)

            if run_duration_seconds and (time.time() - start_time) >= run_duration_seconds:
                log.info("⏱️  Duration limit reached. Stopping producer.")
                break

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        log.info("🛑 Claims producer stopped by user.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediFlow360 Claims Kafka Producer")
    parser.add_argument("--mode",         choices=["local", "azure"], default="local")
    parser.add_argument("--poll-interval", type=int, default=POLL_INTERVAL_SEC)
    parser.add_argument("--duration",     type=int, default=None)
    parser.add_argument("--bootstrap",    type=str, default=None)
    parser.add_argument("--event-hub-ns", type=str, default=None)
    parser.add_argument("--event-hub-key",type=str, default=None)
    args = parser.parse_args()

    if args.mode == "local":
        run_claims_producer(
            bootstrap_servers=args.bootstrap or "localhost:9092",
            poll_interval=args.poll_interval,
            run_duration_seconds=args.duration,
        )
    else:
        ns  = args.event_hub_ns
        key = args.event_hub_key
        if not ns or not key:
            raise ValueError("--event-hub-ns and --event-hub-key required for azure mode")
        run_claims_producer(
            bootstrap_servers=f"{ns}.servicebus.windows.net:9093",
            poll_interval=args.poll_interval,
            use_sasl=True,
            sasl_config={"username": "$ConnectionString", "password": key},
            run_duration_seconds=args.duration,
        )
