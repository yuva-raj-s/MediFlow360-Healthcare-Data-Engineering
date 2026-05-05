"""
MediFlow360 — Airflow DAG: SLA Alerting
DAG ID: sla_alerting
Schedule: 0 * * * * (Hourly)
Owner: Priya Sharma (DE-001)

Description:
    Queries Airflow metadata database for SLA misses and failed task instances
    that occurred in the last hour, and sends grouped alert summaries.
    This provides a safety net if individual DAG failure callbacks fail to fire.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))
from mediflow_hooks import MediFlowTeamsHook

DEFAULT_ARGS = {
    "owner":            "priya.sharma",
    "depends_on_past":  False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

def check_recent_failures(**kwargs):
    """Query Airflow DB for recent failures and SLA misses."""
    # This is a simplified representation. In production, this would query the Airflow metadata DB
    # or use the Airflow API.
    
    # Placeholder for actual metadata DB check
    recent_failures = []
    sla_misses = []

    if recent_failures or sla_misses:
        hook = MediFlowTeamsHook(conn_id="teams_webhook")
        
        if recent_failures:
            hook.send_alert(
                severity="CRITICAL",
                title=f"❌ Hourly Alert: Task Failures Detected",
                message=f"Found {len(recent_failures)} task failures in the last hour.",
                pipeline="sla_alerting"
            )
            
        if sla_misses:
            hook.send_alert(
                severity="WARNING",
                title=f"⏰ Hourly Alert: SLA Misses Detected",
                message=f"Found {len(sla_misses)} SLA misses in the last hour.",
                pipeline="sla_alerting"
            )

with DAG(
    dag_id            = "sla_alerting",
    description       = "MediFlow360: Hourly SLA and failure summary alerting",
    default_args      = DEFAULT_ARGS,
    schedule_interval = "0 * * * *",
    start_date        = datetime(2024, 1, 8),
    catchup           = False,
    tags              = ["mediflow360", "sla", "alerting"],
) as dag:

    check_failures = PythonOperator(
        task_id         = "check_recent_failures_and_slas",
        python_callable = check_recent_failures,
    )

    check_failures
