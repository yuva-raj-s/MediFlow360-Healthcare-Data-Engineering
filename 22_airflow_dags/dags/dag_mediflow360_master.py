"""
MediFlow360 — Airflow DAG: Master Orchestrator
DAG ID: mediflow360_master
Schedule: Manual / Webhook trigger only
Owner: Priya Sharma (DE-001)

Description:
    Master DAG that provides a single-trigger entry point for a full
    end-to-end pipeline run (for manual reruns, incident recovery, or
    initial data loads). Triggers all child DAGs in dependency order:
    
    bronze_batch_ingestion → data_quality_gate → silver_transform → gold_aggregation
    
    The Kafka streaming DAG (kafka_stream_monitor) is always-on and independent.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.trigger_rule import TriggerRule
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))
from mediflow_hooks import MediFlowTeamsHook

DEFAULT_ARGS = {
    "owner":            "priya.sharma",
    "depends_on_past":  False,
    "retries":          0,   # Master DAG does not retry; child DAGs handle retries
}


def on_master_start(**kwargs):
    hook = MediFlowTeamsHook(conn_id="teams_webhook")
    hook.send_alert(
        severity = "INFO",
        title    = "🚀 MediFlow360 Master Pipeline STARTED",
        message  = f"Full pipeline triggered | Run: {kwargs['run_id']} | Date: {kwargs['ds']}",
        pipeline = "mediflow360_master",
    )


def on_master_complete(**kwargs):
    hook = MediFlowTeamsHook(conn_id="teams_webhook")
    hook.send_alert(
        severity = "INFO",
        title    = "🏁 MediFlow360 Master Pipeline COMPLETE",
        message  = f"All layers processed successfully | Run: {kwargs['run_id']} | Date: {kwargs['ds']}",
        pipeline = "mediflow360_master",
    )


with DAG(
    dag_id            = "mediflow360_master",
    description       = "MediFlow360: Master orchestrator — full end-to-end pipeline trigger",
    default_args      = DEFAULT_ARGS,
    schedule_interval = None,   # Manual trigger only
    start_date        = datetime(2024, 1, 8),
    catchup           = False,
    max_active_runs   = 1,
    tags              = ["mediflow360", "master", "orchestrator"],
    doc_md            = """
## MediFlow360 Master Orchestrator

Triggers the complete data pipeline in sequential dependency order.
Use this for:
- Full data backfill runs
- Post-incident recovery
- Initial deployment validation

**Do NOT use** for normal daily operations (child DAGs handle scheduling independently).
""",
) as dag:

    start_notification = EmptyOperator(
        task_id="pipeline_start",
        on_execute_callback=on_master_start,
    )

    # Step 1: Bronze ingestion (batch)
    trigger_bronze = TriggerDagRunOperator(
        task_id             = "trigger_bronze_ingestion",
        trigger_dag_id      = "bronze_batch_ingestion",
        conf                = {"triggered_by": "mediflow360_master", "run_date": "{{ ds }}"},
        wait_for_completion = True,
        poke_interval       = 60,
        allowed_states      = ["success"],
        failed_states       = ["failed"],
    )

    # Step 2: DQ Gate (waits for bronze completion internally)
    trigger_dq = TriggerDagRunOperator(
        task_id             = "trigger_dq_gate",
        trigger_dag_id      = "data_quality_gate",
        conf                = {"triggered_by": "mediflow360_master", "run_date": "{{ ds }}"},
        wait_for_completion = True,
        poke_interval       = 30,
        allowed_states      = ["success"],
        failed_states       = ["failed"],
    )

    # Step 3: Silver transformation
    trigger_silver = TriggerDagRunOperator(
        task_id             = "trigger_silver_transform",
        trigger_dag_id      = "silver_transform",
        conf                = {"triggered_by": "mediflow360_master", "run_date": "{{ ds }}"},
        wait_for_completion = True,
        poke_interval       = 60,
        allowed_states      = ["success"],
        failed_states       = ["failed"],
    )

    # Step 4: Gold aggregation
    trigger_gold = TriggerDagRunOperator(
        task_id             = "trigger_gold_aggregation",
        trigger_dag_id      = "gold_aggregation",
        conf                = {"triggered_by": "mediflow360_master", "run_date": "{{ ds }}"},
        wait_for_completion = True,
        poke_interval       = 60,
        allowed_states      = ["success"],
        failed_states       = ["failed"],
    )

    end_notification = EmptyOperator(
        task_id         = "pipeline_complete",
        on_execute_callback = on_master_complete,
        trigger_rule    = TriggerRule.ALL_DONE,
    )

    (
        start_notification
        >> trigger_bronze
        >> trigger_dq
        >> trigger_silver
        >> trigger_gold
        >> end_notification
    )
