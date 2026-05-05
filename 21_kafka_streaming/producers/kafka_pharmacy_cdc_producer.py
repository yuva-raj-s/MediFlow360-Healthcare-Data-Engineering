"""
MediFlow360 — Kafka Pharmacy CDC Producer
Source: S5 PostgreSQL Pharmacy (Logical WAL Replication via Debezium) → Kafka Topic: mrhs.pharmacy.cdc
Author: Kavitha Rajan (DE-003)
Version: 1.0 | Date: 2024-04-03

Description:
    Forwards Change Data Capture (CDC) events from the PostgreSQL pharmacy
    database (logical replication slot via Debezium connector) into Kafka.
    In production, Debezium runs as a Kafka Connect connector and writes
    directly to the topic. This script simulates CDC events for local dev.

    CDC Event Model (Debezium envelope):
        op              : str  — "c" (create) | "u" (update) | "d" (delete) | "r" (read/snapshot)
        source.table    : str  — postgres table name
        before          : dict — Row state before change (null for inserts)
        after           : dict — Row state after change (null for deletes)
        ts_ms           : int  — Event timestamp (Unix ms)
        transaction.id  : str  — PostgreSQL transaction ID

    Tables tracked:
        pharmacy.drug_inventory    — Stock levels, expiry, reorder
        pharmacy.prescriptions     — Active/filled prescriptions
        pharmacy.dispensing_log    — Medication dispensing events
"""

import json
import time
import random
import logging
import argparse
from datetime import datetime, timezone, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("KafkaPharmacyCDCProducer")

# ── Constants ──────────────────────────────────────────────────────────────────
TOPIC_PHARMACY_CDC  = "mrhs.pharmacy.cdc"

CDC_TABLES = ["drug_inventory", "prescriptions", "dispensing_log"]
CDC_OPS    = ["c", "u", "d", "r"]

# Sample drug catalog (NDC codes: MRHS formulary)
DRUG_CATALOG = [
    {"ndc": "00006-0749-54", "name": "Metformin 500mg",    "category": "Antidiabetic"},
    {"ndc": "00093-0058-01", "name": "Atorvastatin 10mg",  "category": "Statin"},
    {"ndc": "00025-1550-31", "name": "Amlodipine 5mg",     "category": "Antihypertensive"},
    {"ndc": "00006-0163-68", "name": "Furosemide 40mg",    "category": "Diuretic"},
    {"ndc": "00071-0155-24", "name": "Pantoprazole 40mg",  "category": "PPI"},
    {"ndc": "00006-0952-54", "name": "Insulin Glargine",   "category": "Insulin"},
    {"ndc": "00069-0562-66", "name": "Azithromycin 500mg", "category": "Antibiotic"},
    {"ndc": "00378-0221-93", "name": "Warfarin 5mg",       "category": "Anticoagulant"},
]

HOSPITALS = ["CHN", "MDU", "CBE", "TRV"]


def build_cdc_envelope(op: str, table: str, before: dict, after: dict, txn_id: str) -> dict:
    """Construct a Debezium-compatible CDC envelope."""
    return {
        "schema": {
            "type":   "struct",
            "name":   f"mrhs.pharmacy.{table}.Envelope",
            "version": 1,
        },
        "payload": {
            "op":     op,
            "before": before,
            "after":  after,
            "source": {
                "version":    "2.5.0.Final",
                "connector":  "postgresql",
                "name":       "mrhs-postgres-pharmacy",
                "ts_ms":      int(datetime.now(timezone.utc).timestamp() * 1000),
                "db":         "pharmacy_db",
                "schema":     "pharmacy",
                "table":      table,
                "txId":       txn_id,
                "lsn":        random.randint(1000000, 9999999),
            },
            "ts_ms":  int(datetime.now(timezone.utc).timestamp() * 1000),
            "transaction": {
                "id":                  txn_id,
                "total_order":         1,
                "data_collection_order": 1,
            }
        }
    }


def generate_drug_inventory_cdc(op: str) -> dict:
    """Generate a drug_inventory CDC event."""
    drug    = random.choice(DRUG_CATALOG)
    hosp    = random.choice(HOSPITALS)
    inv_id  = f"INV-{hosp}-{str(random.randint(1, 9999)).zfill(5)}"
    qty     = random.randint(0, 500)
    reorder = random.randint(20, 100)
    expiry  = (datetime.now(timezone.utc) + timedelta(days=random.randint(30, 730))).date().isoformat()

    row = {
        "inventory_id":   inv_id,
        "ndc_code":       drug["ndc"],
        "drug_name":      drug["name"],
        "drug_category":  drug["category"],
        "hospital_code":  hosp,
        "quantity_units": qty,
        "reorder_level":  reorder,
        "expiry_date":    expiry,
        "unit_cost_inr":  round(random.uniform(5.0, 1200.0), 2),
        "is_critical":    qty < reorder,
        "updated_at":     datetime.now(timezone.utc).isoformat(),
    }

    before = row.copy() if op in ("u", "d") else None
    after  = row if op in ("c", "u", "r") else None

    if op == "u" and after:
        after["quantity_units"] = max(0, row["quantity_units"] - random.randint(1, 50))
        after["is_critical"]    = after["quantity_units"] < reorder

    return build_cdc_envelope(op, "drug_inventory", before, after, f"TXN-{random.randint(100000, 999999)}")


def generate_dispensing_log_cdc() -> dict:
    """Generate a dispensing_log INSERT event (only 'c' ops for dispensing)."""
    drug  = random.choice(DRUG_CATALOG)
    hosp  = random.choice(HOSPITALS)
    row   = {
        "dispense_id":      f"DISP-{hosp}-{str(random.randint(1, 99999)).zfill(6)}",
        "prescription_id":  f"RX-{str(random.randint(1, 99999)).zfill(7)}",
        "patient_mrn":      f"MRN-{hosp}-{str(random.randint(1, 9999)).zfill(5)}",
        "ndc_code":         drug["ndc"],
        "drug_name":        drug["name"],
        "quantity_dispensed": random.randint(1, 90),
        "pharmacist_id":    f"PHARM-{random.randint(1, 50):03d}",
        "hospital_code":    hosp,
        "dispensed_at":     datetime.now(timezone.utc).isoformat(),
        "lot_number":       f"LOT{random.randint(100000, 999999)}",
    }
    return build_cdc_envelope("c", "dispensing_log", None, row, f"TXN-{random.randint(100000, 999999)}")


def get_kafka_producer(bootstrap_servers: str, use_sasl: bool = False, sasl_config: dict = None) -> KafkaProducer:
    """Create Kafka producer for CDC events."""
    config = {
        "bootstrap_servers": bootstrap_servers,
        "value_serializer":  lambda v: json.dumps(v).encode("utf-8"),
        "key_serializer":    lambda k: k.encode("utf-8") if k else None,
        "acks":              "all",
        "retries":           5,
        "compression_type":  "gzip",
        "linger_ms":         20,
    }
    if use_sasl and sasl_config:
        config.update({
            "security_protocol":   "SASL_SSL",
            "sasl_mechanism":      "PLAIN",
            "sasl_plain_username": sasl_config["username"],
            "sasl_plain_password": sasl_config["password"],
        })
    return KafkaProducer(**config)


def run_cdc_producer(
    bootstrap_servers: str,
    rate_per_second: int = 2,
    use_sasl: bool = False,
    sasl_config: dict = None,
    run_duration_seconds: int = None,
):
    """
    Main CDC event simulation loop.
    Generates a mix of drug_inventory updates and dispensing_log inserts.
    """
    producer  = get_kafka_producer(bootstrap_servers, use_sasl, sasl_config)
    total_sent = 0
    start_time = time.time()
    sleep_interval = 1.0 / max(rate_per_second, 1)

    log.info("🚀 Pharmacy CDC Producer started | Topic: %s | Rate: %d msg/s", TOPIC_PHARMACY_CDC, rate_per_second)

    try:
        while True:
            # Mix of CDC event types
            event_type = random.choices(
                ["inventory_update", "inventory_insert", "dispensing"],
                weights=[50, 20, 30],
            )[0]

            if event_type == "inventory_update":
                event = generate_drug_inventory_cdc("u")
                key   = event["payload"]["after"]["inventory_id"]
            elif event_type == "inventory_insert":
                event = generate_drug_inventory_cdc("c")
                key   = event["payload"]["after"]["inventory_id"]
            else:
                event = generate_dispensing_log_cdc()
                key   = event["payload"]["after"]["dispense_id"]

            try:
                producer.send(TOPIC_PHARMACY_CDC, key=key, value=event)
                total_sent += 1
            except KafkaError as ke:
                log.error("❌ Failed to send CDC event: %s", ke)

            if total_sent % 50 == 0:
                producer.flush()
                elapsed = time.time() - start_time
                log.info("📊 Progress | Sent: %d | Elapsed: %.1fs | Rate: %.1f msg/s",
                          total_sent, elapsed, total_sent / elapsed)

            if run_duration_seconds and (time.time() - start_time) >= run_duration_seconds:
                log.info("⏱️  Duration limit reached. Stopping.")
                break

            time.sleep(sleep_interval)

    except KeyboardInterrupt:
        log.info("🛑 CDC producer stopped.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediFlow360 Pharmacy CDC Kafka Producer")
    parser.add_argument("--mode",          choices=["local", "azure"], default="local")
    parser.add_argument("--rate",          type=int, default=2)
    parser.add_argument("--duration",      type=int, default=None)
    parser.add_argument("--bootstrap",     type=str, default=None)
    parser.add_argument("--event-hub-ns",  type=str, default=None)
    parser.add_argument("--event-hub-key", type=str, default=None)
    args = parser.parse_args()

    if args.mode == "local":
        run_cdc_producer(
            bootstrap_servers=args.bootstrap or "localhost:9092",
            rate_per_second=args.rate,
            run_duration_seconds=args.duration,
        )
    else:
        run_cdc_producer(
            bootstrap_servers=f"{args.event_hub_ns}.servicebus.windows.net:9093",
            rate_per_second=args.rate,
            use_sasl=True,
            sasl_config={"username": "$ConnectionString", "password": args.event_hub_key},
            run_duration_seconds=args.duration,
        )
