"""
MediFlow360 — Airflow DAG: Kafka Stream Monitor
DAG ID: kafka_stream_monitor
Schedule: */2 * * * * (every 2 minutes)
Owner: Kavitha Rajan (DE-003)
SLA: 2 minutes (self-monitoring)

Description:
    Continuously monitors Kafka consumer lag for all MediFlow360 streaming topics.
    If consumer lag exceeds configured thresholds, this DAG:
      1. Sends a WARNING alert to Teams
      2. Optionally triggers a Databricks cluster scale-up job
      3. Logs the lag metric to Azure Monitor

    Topics monitored:
        mrhs.icu.vitals       — threshold: 500 records
        mrhs.insurance.claims — threshold: 200 records
        mrhs.pharmacy.cdc     — threshold: 100 records
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))
from mediflow_hooks import MediFlowTeamsHook

# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_ARGS = {
    "owner":            "kavitha.rajan",
    "depends_on_past":  False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=1),
    "email_on_failure": False,   # Teams alert handles notifications
}

# Lag thresholds per topic
LAG_THRESHOLDS = {
    "mrhs.icu.vitals":        500,
    "mrhs.insurance.claims":  200,
    "mrhs.pharmacy.cdc":      100,
}

CONSUMER_GROUPS = {
    "mrhs.icu.vitals":       "mediflow360-vitals-consumer-grp",
    "mrhs.insurance.claims": "mediflow360-claims-consumer-grp",
    "mrhs.pharmacy.cdc":     "mediflow360-pharmacy-cdc-grp",
}


def check_kafka_consumer_lag(**kwargs):
    """
    Poll Kafka consumer group lag via AdminClient.
    In production: connects to Azure Event Hubs REST API or confluent-kafka AdminClient.
    Pushes lag metrics to XCom for downstream tasks.
    """
    import random  # Replace with actual Kafka AdminClient calls in production

    lag_results = {}
    breached_topics = []

    for topic, group in CONSUMER_GROUPS.items():
        # Production: use confluent_kafka.admin.AdminClient to get consumer lag
        # simulated_lag = admin_client.list_consumer_group_offsets(group, [TopicPartition(topic)])
        simulated_lag = random.randint(0, 600)   # Simulate lag 0–600

        threshold = LAG_THRESHOLDS.get(topic, 1000)
        status    = "OK" if simulated_lag <= threshold else "BREACHED"

        lag_results[topic] = {
            "consumer_group": group,
            "lag":            simulated_lag,
            "threshold":      threshold,
            "status":         status,
            "checked_at":     datetime.utcnow().isoformat(),
        }

        if status == "BREACHED":
            breached_topics.append(topic)

        print(f"[LagMonitor] {topic}: lag={simulated_lag} | threshold={threshold} | status={status}")

    kwargs["ti"].xcom_push(key="lag_results",     value=lag_results)
    kwargs["ti"].xcom_push(key="breached_topics", value=breached_topics)
    kwargs["ti"].xcom_push(key="breach_count",    value=len(breached_topics))

    return lag_results


def send_lag_alert_if_breached(**kwargs):
    """Send Teams alert for each breached topic."""
    ti              = kwargs["ti"]
    lag_results     = ti.xcom_pull(task_ids="check_consumer_lag", key="lag_results") or {}
    breached_topics = ti.xcom_pull(task_ids="check_consumer_lag", key="breached_topics") or []

    if not breached_topics:
        print("[LagMonitor] ✅ All topics within lag threshold.")
        return "no_breach"

    hook = MediFlowTeamsHook(conn_id="teams_webhook")

    details = []
    for topic in breached_topics:
        r = lag_results[topic]
        details.append(
            f"**{topic}**: lag={r['lag']} | threshold={r['threshold']} | "
            f"group={r['consumer_group']}"
        )

    hook.send_alert(
        severity = "WARNING",
        title    = f"⚠️ Kafka Consumer Lag Breach — {len(breached_topics)} topic(s)",
        message  = "\n".join(details),
        pipeline = "kafka_stream_monitor",
        entity   = ", ".join(breached_topics),
    )

    print(f"[LagMonitor] ⚠️  Alert sent for {len(breached_topics)} breached topics.")
    return "breach_detected"


def log_lag_metrics_to_azure_monitor(**kwargs):
    """
    Push consumer lag metrics to Azure Monitor custom metrics endpoint.
    In production: use azure-monitor-opentelemetry-exporter or REST API.
    """
    ti          = kwargs["ti"]
    lag_results = ti.xcom_pull(task_ids="check_consumer_lag", key="lag_results") or {}

    for topic, result in lag_results.items():
        metric_name  = f"KafkaConsumerLag_{topic.replace('.', '_')}"
        metric_value = result["lag"]
        # Production: push to Azure Monitor
        # AzureMonitorMetric(name=metric_name, value=metric_value, dimensions={...}).publish()
        print(f"[LagMonitor] 📊 Azure Monitor: {metric_name} = {metric_value}")


def trigger_databricks_scale_up(**kwargs):
    """
    If critical lag breach detected, trigger Databricks cluster scale-up
    via the Databricks Jobs REST API (resize running cluster).
    """
    ti            = kwargs["ti"]
    breach_count  = ti.xcom_pull(task_ids="check_consumer_lag", key="breach_count") or 0
    breached      = ti.xcom_pull(task_ids="check_consumer_lag", key="breached_topics") or []

    if breach_count == 0:
        print("[LagMonitor] No breaches. Scale-up not needed.")
        return

    # Production: use DatabricksHook to resize cluster
    # hook = DatabricksHook(conn_id="databricks_default")
    # hook.resize_cluster(cluster_id=STREAMING_CLUSTER_ID, num_workers=MAX_WORKERS)
    print(f"[LagMonitor] 🔼 Triggered scale-up for streaming cluster. Breached: {breached}")


# ─────────────────────────────────────────────────────────────────────────────
# DAG
# ─────────────────────────────────────────────────────────────────────────────
with DAG(
    dag_id            = "kafka_stream_monitor",
    description       = "MediFlow360: Monitor Kafka consumer lag and trigger auto-scaling",
    default_args      = DEFAULT_ARGS,
    schedule_interval = "*/2 * * * *",
    start_date        = datetime(2024, 4, 1),
    catchup           = False,
    max_active_runs   = 1,
    tags              = ["mediflow360", "kafka", "streaming", "monitoring", "realtime"],
    doc_md            = """
## Kafka Stream Monitor DAG

Runs every **2 minutes** to check Kafka consumer lag for all streaming topics.
Triggers auto-scaling if lag breaches configured thresholds.
""",
) as dag:

    start = EmptyOperator(task_id="start_lag_check")

    check_lag = PythonOperator(
        task_id         = "check_consumer_lag",
        python_callable = check_kafka_consumer_lag,
    )

    alert_task = PythonOperator(
        task_id         = "send_lag_alert",
        python_callable = send_lag_alert_if_breached,
    )

    log_metrics = PythonOperator(
        task_id         = "log_metrics_to_azure_monitor",
        python_callable = log_lag_metrics_to_azure_monitor,
    )

    scale_up = PythonOperator(
        task_id         = "trigger_scale_up_if_needed",
        python_callable = trigger_databricks_scale_up,
    )

    end = EmptyOperator(task_id="end_lag_check", trigger_rule=TriggerRule.ALL_DONE)

    start >> check_lag >> [alert_task, log_metrics, scale_up] >> end
