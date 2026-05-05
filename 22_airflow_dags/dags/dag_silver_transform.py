"""
MediFlow360 — Airflow DAG: Silver Transformation
DAG ID: silver_transform
Schedule: 0 6 * * * (Daily at 6:00 AM IST = 00:30 UTC)
Owner: Priya Sharma (DE-001)
SLA: 2 hours | Depends on: bronze_batch_ingestion (ExternalTaskSensor)

Description:
    Orchestrates the Silver layer transformation pipeline:
    1. Waits for Bronze ingestion to complete (ExternalTaskSensor)
    2. Runs Silver Transform notebook via Databricks Jobs API
    3. Runs SCD Type-2 notebook for patient dimension
    4. Triggers DQ gate after Silver promotion
    5. Triggers Gold aggregation DAG on success
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.trigger_rule import TriggerRule
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))
from databricks_operator import DatabricksNotebookOperator
from mediflow_hooks import MediFlowTeamsHook

DEFAULT_ARGS = {
    "owner":             "priya.sharma",
    "depends_on_past":   False,
    "email":             ["priya.sharma@mrhs-de.in"],
    "email_on_failure":  True,
    "retries":           2,
    "retry_delay":       timedelta(minutes=15),
}

DATABRICKS_CONN_ID   = "databricks_default"
DATABRICKS_CLUSTER   = "{{var.value.databricks_silver_cluster_id}}"


def on_failure_callback(context):
    hook = MediFlowTeamsHook(conn_id="teams_webhook")
    hook.send_alert(
        severity="CRITICAL",
        title=f"❌ SILVER TRANSFORM FAILED: {context['task_instance'].task_id}",
        message=f"Run ID: {context['run_id']} | Error: {context.get('exception', 'Unknown')}",
        pipeline="silver_transform",
    )


with DAG(
    dag_id            = "silver_transform",
    description       = "MediFlow360: Silver transformation pipeline with SCD2 and DQ gate",
    default_args      = DEFAULT_ARGS,
    schedule_interval = "30 0 * * *",   # 00:30 UTC = 06:00 IST
    start_date        = datetime(2024, 1, 8),
    catchup           = False,
    max_active_runs   = 1,
    tags              = ["mediflow360", "silver", "transform", "scd2"],
) as dag:

    start = EmptyOperator(task_id="start_silver")

    # Wait for bronze ingestion to complete
    wait_bronze = ExternalTaskSensor(
        task_id              = "wait_for_bronze_completion",
        external_dag_id      = "bronze_batch_ingestion",
        external_task_id     = "end_bronze_ingestion",
        allowed_states       = ["success"],
        failed_states        = ["failed", "skipped"],
        execution_delta      = timedelta(hours=4),   # Bronze runs 4h earlier (IST offset)
        timeout              = 7200,
        poke_interval        = 120,
        mode                 = "reschedule",
        on_failure_callback  = on_failure_callback,
    )

    # PII masking + Silver transform
    silver_transform = DatabricksNotebookOperator(
        task_id          = "run_silver_transform",
        databricks_conn_id = DATABRICKS_CONN_ID,
        notebook_path    = "/MediFlow360/07_notebooks/02_Silver_Transform_NB",
        notebook_params  = {
            "pipeline_run_id": "{{ run_id }}",
            "run_date":        "{{ ds }}",
            "source_system":   "ALL",
        },
        cluster_id       = DATABRICKS_CLUSTER,
        polling_period_seconds = 60,
        sla              = timedelta(hours=1),
        on_failure_callback = on_failure_callback,
    )

    # SCD Type-2 for patient dimension
    scd2_patients = DatabricksNotebookOperator(
        task_id          = "run_scd2_patients",
        databricks_conn_id = DATABRICKS_CONN_ID,
        notebook_path    = "/MediFlow360/07_notebooks/02b_Silver_SCD2_NB",
        notebook_params  = {
            "pipeline_run_id": "{{ run_id }}",
            "run_date":        "{{ ds }}",
            "entity":          "patients",
        },
        cluster_id       = DATABRICKS_CLUSTER,
        polling_period_seconds = 60,
        on_failure_callback = on_failure_callback,
    )

    # SCD Type-3 for pharmacy changes
    scd3_pharmacy = DatabricksNotebookOperator(
        task_id          = "run_scd3_pharmacy",
        databricks_conn_id = DATABRICKS_CONN_ID,
        notebook_path    = "/MediFlow360/07_notebooks/02c_Silver_SCD3_NB",
        notebook_params  = {
            "pipeline_run_id": "{{ run_id }}",
            "run_date":        "{{ ds }}",
        },
        cluster_id       = DATABRICKS_CLUSTER,
        polling_period_seconds = 60,
        on_failure_callback = on_failure_callback,
    )

    # Anomaly detection
    anomaly_detect = DatabricksNotebookOperator(
        task_id          = "run_anomaly_detection",
        databricks_conn_id = DATABRICKS_CONN_ID,
        notebook_path    = "/MediFlow360/07_notebooks/04_Anomaly_Detection_NB",
        notebook_params  = {"pipeline_run_id": "{{ run_id }}", "run_date": "{{ ds }}"},
        cluster_id       = DATABRICKS_CLUSTER,
        polling_period_seconds = 60,
        on_failure_callback = on_failure_callback,
    )

    # Trigger Gold aggregation
    trigger_gold = TriggerDagRunOperator(
        task_id         = "trigger_gold_aggregation",
        trigger_dag_id  = "gold_aggregation",
        conf            = {"triggered_by": "silver_transform", "run_date": "{{ ds }}"},
        wait_for_completion = False,
    )

    end = EmptyOperator(task_id="end_silver", trigger_rule=TriggerRule.ALL_DONE)

    (
        start
        >> wait_bronze
        >> silver_transform
        >> [scd2_patients, scd3_pharmacy]
        >> anomaly_detect
        >> trigger_gold
        >> end
    )
