"""
MediFlow360 — Kafka ICU Vitals Producer
Source: S7 ICU Monitors (IoT Hub / MQTT) → Kafka Topic: mrhs.icu.vitals
Author: Arjun Patel (DE-002)
Version: 1.0 | Date: 2024-04-01

Description:
    Simulates and forwards real-time ICU vital sign readings from the
    Azure IoT Hub (MQTT) into a Kafka topic for Spark Structured Streaming.
    In production, an Azure IoT Hub → Event Hub bridge is used. This script
    simulates the producer for local dev and integration testing.

    Data Model (ICU Vitals):
        device_id       : str  — "ICU-BED-{HOSPITAL}-{BED_NO}"
        patient_mrn     : str  — Patient medical record number
        heart_rate      : int  — BPM (60–120 normal range)
        spo2            : float — SpO2 % (95–100 normal)
        systolic_bp     : int  — mmHg
        diastolic_bp    : int  — mmHg
        temperature_c   : float — °C
        respiratory_rate: int  — breaths/min
        recorded_at     : str  — ISO 8601 UTC timestamp
        hospital_code   : str  — CHN | MDU | CBE | TRV
"""

import json
import time
import random
import argparse
import logging
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("KafkaVitalsProducer")

# ── Constants ──────────────────────────────────────────────────────────────────
TOPIC_ICU_VITALS = "mrhs.icu.vitals"

HOSPITAL_CODES = ["CHN", "MDU", "CBE", "TRV"]
BEDS_PER_HOSPITAL = 20

# Simulated patient MRNs (in prod, resolved from HIS MySQL)
PATIENT_MRNS = [f"MRN-{h}-{str(i).zfill(5)}" for h in HOSPITAL_CODES for i in range(1, 21)]

# Alert thresholds (for producer-side validation logging)
ALERT_THRESHOLDS = {
    "heart_rate":        {"low": 45, "high": 130},
    "spo2":              {"low": 90.0, "high": 100.0},
    "systolic_bp":       {"low": 80, "high": 180},
    "temperature_c":     {"low": 35.0, "high": 40.0},
    "respiratory_rate":  {"low": 8, "high": 30},
}


def get_kafka_producer(bootstrap_servers: str, use_sasl: bool = False, sasl_config: dict = None) -> KafkaProducer:
    """
    Create a KafkaProducer with JSON serialization.
    For Azure Event Hubs, use SASL_SSL with the Event Hub connection string as the password.
    
    Azure Event Hubs Kafka endpoint:
        Bootstrap server: <namespace>.servicebus.windows.net:9093
        SASL mechanism:   PLAIN
        Username:         $ConnectionString
        Password:         <Event Hub connection string>
    """
    config = {
        "bootstrap_servers": bootstrap_servers,
        "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
        "key_serializer":   lambda k: k.encode("utf-8") if k else None,
        "acks":             "all",              # Wait for all replicas to acknowledge
        "retries":          5,
        "retry_backoff_ms": 300,
        "compression_type": "gzip",
        "linger_ms":        10,                 # Micro-batch for throughput
        "batch_size":       16384,
    }

    if use_sasl and sasl_config:
        config.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism":    "PLAIN",
            "sasl_plain_username": sasl_config["username"],
            "sasl_plain_password": sasl_config["password"],
            "ssl_check_hostname":  True,
        })

    return KafkaProducer(**config)


def generate_vital_reading(hospital_code: str, bed_no: int, anomaly_rate: float = 0.05) -> dict:
    """
    Generate a realistic ICU vital sign reading.
    anomaly_rate: probability (0–1) of injecting an out-of-range value to test alerts.
    """
    is_anomaly = random.random() < anomaly_rate
    patient_mrn = f"MRN-{hospital_code}-{str(bed_no).zfill(5)}"
    device_id   = f"ICU-BED-{hospital_code}-{str(bed_no).zfill(3)}"

    # Normal ranges with slight variance
    heart_rate        = random.randint(55, 110) if not is_anomaly else random.choice([random.randint(35, 44), random.randint(131, 180)])
    spo2              = round(random.uniform(95.0, 99.9), 1) if not is_anomaly else round(random.uniform(80.0, 89.9), 1)
    systolic_bp       = random.randint(100, 140) if not is_anomaly else random.randint(181, 220)
    diastolic_bp      = random.randint(60, 90)
    temperature_c     = round(random.uniform(36.2, 37.8), 1) if not is_anomaly else round(random.uniform(38.5, 41.0), 1)
    respiratory_rate  = random.randint(12, 22) if not is_anomaly else random.randint(31, 45)

    reading = {
        "event_type":        "vitals_reading",
        "schema_version":    "1.2",
        "device_id":         device_id,
        "patient_mrn":       patient_mrn,
        "hospital_code":     hospital_code,
        "bed_number":        bed_no,
        "heart_rate":        heart_rate,
        "spo2":              spo2,
        "systolic_bp":       systolic_bp,
        "diastolic_bp":      diastolic_bp,
        "temperature_c":     temperature_c,
        "respiratory_rate":  respiratory_rate,
        "is_anomaly_injected": is_anomaly,        # For testing only — remove in prod
        "recorded_at":       datetime.now(timezone.utc).isoformat(),
        "ingestion_source":  "ICU_MONITOR_SIMULATOR_v1.0",
    }

    # Log anomalies
    if is_anomaly:
        log.warning(
            "⚠️  ANOMALY INJECTED | Device: %s | HR: %s | SpO2: %s | SysBP: %s | Temp: %s",
            device_id, heart_rate, spo2, systolic_bp, temperature_c
        )

    return reading


def delivery_report_callback(err, msg):
    """Callback for async send — logs delivery success/failure."""
    if err is not None:
        log.error("❌ Message delivery FAILED: %s | Topic: %s | Partition: %s", err, msg.topic(), msg.partition())
    else:
        log.debug("✅ Delivered → Topic: %s | Partition: %d | Offset: %d", msg.topic(), msg.partition(), msg.offset())


def run_producer(
    bootstrap_servers: str,
    rate_per_second: int = 10,
    use_sasl: bool = False,
    sasl_config: dict = None,
    run_duration_seconds: int = None,
    anomaly_rate: float = 0.05,
):
    """
    Main producer loop.
    
    Args:
        bootstrap_servers: Kafka broker(s) — "localhost:9092" or Event Hubs endpoint
        rate_per_second:   Messages to send per second (across all beds)
        use_sasl:          True for Azure Event Hubs (SASL_SSL)
        sasl_config:       Dict with 'username' and 'password'
        run_duration_seconds: None = run indefinitely; int = stop after N seconds
        anomaly_rate:      0.0–1.0 probability of injecting anomalous readings
    """
    producer = get_kafka_producer(bootstrap_servers, use_sasl, sasl_config)
    log.info("🚀 ICU Vitals Producer started | Topic: %s | Rate: %d msg/s", TOPIC_ICU_VITALS, rate_per_second)

    total_sent = 0
    start_time = time.time()
    sleep_interval = 1.0 / max(rate_per_second, 1)

    try:
        while True:
            # Cycle through all hospital beds
            hospital = random.choice(HOSPITAL_CODES)
            bed_no   = random.randint(1, BEDS_PER_HOSPITAL)

            payload = generate_vital_reading(hospital, bed_no, anomaly_rate)
            key     = payload["device_id"]

            try:
                producer.send(
                    topic=TOPIC_ICU_VITALS,
                    key=key,
                    value=payload,
                ).add_errback(lambda exc: log.error("Kafka send error: %s", exc))
                total_sent += 1

            except KafkaError as ke:
                log.error("Kafka send error: %s", ke)

            # Flush every 100 messages
            if total_sent % 100 == 0:
                producer.flush()
                elapsed = time.time() - start_time
                log.info("📊 Progress | Sent: %d | Elapsed: %.1fs | Rate: %.1f msg/s",
                          total_sent, elapsed, total_sent / elapsed)

            # Check duration limit
            if run_duration_seconds and (time.time() - start_time) >= run_duration_seconds:
                log.info("⏱️  Duration limit reached (%ds). Stopping.", run_duration_seconds)
                break

            time.sleep(sleep_interval)

    except KeyboardInterrupt:
        log.info("🛑 Producer interrupted by user.")
    finally:
        producer.flush()
        producer.close()
        elapsed = time.time() - start_time
        log.info("✅ Producer stopped | Total sent: %d | Duration: %.1fs | Avg rate: %.1f msg/s",
                  total_sent, elapsed, total_sent / max(elapsed, 1))


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediFlow360 ICU Vitals Kafka Producer")
    parser.add_argument("--mode",          choices=["local", "azure"], default="local",
                        help="'local' = localhost:9092 | 'azure' = Event Hubs SASL_SSL")
    parser.add_argument("--rate",          type=int,   default=10,       help="Messages per second")
    parser.add_argument("--duration",      type=int,   default=None,     help="Run duration in seconds (None=infinite)")
    parser.add_argument("--anomaly-rate",  type=float, default=0.05,     help="Probability of injecting anomalous vital")
    parser.add_argument("--bootstrap",     type=str,   default=None,     help="Override bootstrap servers")
    parser.add_argument("--event-hub-ns",  type=str,   default=None,     help="Azure Event Hubs namespace (for azure mode)")
    parser.add_argument("--event-hub-key", type=str,   default=None,     help="Event Hubs connection string / SAS key")
    args = parser.parse_args()

    if args.mode == "local":
        servers = args.bootstrap or "localhost:9092"
        run_producer(
            bootstrap_servers=servers,
            rate_per_second=args.rate,
            run_duration_seconds=args.duration,
            anomaly_rate=args.anomaly_rate,
        )
    elif args.mode == "azure":
        if not args.event_hub_ns or not args.event_hub_key:
            raise ValueError("--event-hub-ns and --event-hub-key are required for azure mode")
        servers = f"{args.event_hub_ns}.servicebus.windows.net:9093"
        sasl_cfg = {
            "username": "$ConnectionString",
            "password": args.event_hub_key,
        }
        run_producer(
            bootstrap_servers=servers,
            rate_per_second=args.rate,
            use_sasl=True,
            sasl_config=sasl_cfg,
            run_duration_seconds=args.duration,
            anomaly_rate=args.anomaly_rate,
        )
