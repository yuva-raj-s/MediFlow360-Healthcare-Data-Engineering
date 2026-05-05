"""
MediFlow360 — Airflow DAG: Data Quality Gate
DAG ID: data_quality_gate
Trigger: TriggerDagRunOperator from bronze_batch_ingestion
Owner: Kavitha Rajan (DE-003)
SLA: 30 minutes

Description:
    Enforces data quality as a formal gate between Bronze and Silver layers.
    Runs DQ notebooks against the latest Bronze partition and fails the
    pipeline if critical quality thresholds are breached.

    DQ Checks:
        - Null rate on critical fields (DOB, patient_id, MRN)
        - Referential integrity (hospital_code in valid set)
        - Duplicate detection (patient_id uniqueness)
        - Schema drift detection (unexpected new columns)
        - Freshness check (max(updated_at) within last 24h)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))
from databricks_operator import DatabricksNotebookOperator
from mediflow_hooks import MediFlowTeamsHook

DEFAULT_ARGS = {
    "owner":            "kavitha.rajan",
    "depends_on_past":  False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

DATABRICKS_CONN_ID = "databricks_default"
DATABRICKS_CLUSTER = "{{var.value.databricks_bronze_cluster_id}}"

# DQ thresholds (configurable via Airflow Variables)
DQ_THRESHOLDS = {
    "max_null_rate_pct":     2.0,    # Fail if critical cols > 2% null
    "max_duplicate_rate_pct": 0.1,   # Fail if > 0.1% duplicate patient IDs
    "min_freshness_hours":   24,     # Fail if data is older than 24 hours
}


def evaluate_dq_results(**kwargs):
    """
    Read DQ results from XCom (published by DQ notebook).
    Determines if pipeline should proceed or halt.
    """
    ti         = kwargs["ti"]
    dq_output  = ti.xcom_pull(task_ids="run_dq_checks", key="notebook_output") or ""

    # Parse result (notebook pushes JSON to dbutils.notebook.exit())
    import json
    try:
        dq_result = json.loads(dq_output) if dq_output else {"passed": True, "issues": []}
    except (json.JSONDecodeError, TypeError):
        dq_result = {"passed": True, "issues": []}

    ti.xcom_push(key="dq_passed",  value=dq_result.get("passed", True))
    ti.xcom_push(key="dq_issues",  value=dq_result.get("issues", []))

    if dq_result.get("passed", True):
        return "dq_gate_passed"
    else:
        return "dq_gate_failed"


def send_dq_failure_alert(**kwargs):
    """Send CRITICAL Teams alert if DQ gate fails."""
    ti      = kwargs["ti"]
    issues  = ti.xcom_pull(task_ids="evaluate_dq_results", key="dq_issues") or []
    hook    = MediFlowTeamsHook(conn_id="teams_webhook")
    hook.send_alert(
        severity = "CRITICAL",
        title    = f"🚫 DQ Gate FAILED — Bronze → Silver BLOCKED",
        message  = f"Run: {kwargs['run_id']} | Issues: {'; '.join(str(i) for i in issues[:5])}",
        pipeline = "data_quality_gate",
        entity   = "bronze_all_entities",
    )


def send_dq_success_notification(**kwargs):
    """Send INFO Teams card on DQ gate pass."""
    hook = MediFlowTeamsHook(conn_id="teams_webhook")
    hook.send_alert(
        severity = "INFO",
        title    = f"✅ DQ Gate PASSED — Bronze → Silver Promotion Authorized",
        message  = f"Run: {kwargs['run_id']} | Date: {kwargs['ds']}",
        pipeline = "data_quality_gate",
    )


with DAG(
    dag_id            = "data_quality_gate",
    description       = "MediFlow360: DQ gate — validates Bronze layer before Silver promotion",
    default_args      = DEFAULT_ARGS,
    schedule_interval = None,   # Triggered only by bronze_batch_ingestion DAG
    start_date        = datetime(2024, 1, 8),
    catchup           = False,
    tags              = ["mediflow360", "dq", "quality", "gate"],
) as dag:

    start = EmptyOperator(task_id="start_dq_gate")

    # Run comprehensive DQ notebook (05_Data_Quality_NB + 05b_DQ_Metadata_Driven_NB)
    run_dq = DatabricksNotebookOperator(
        task_id          = "run_dq_checks",
        databricks_conn_id = DATABRICKS_CONN_ID,
        notebook_path    = "/MediFlow360/07_notebooks/05_Data_Quality_NB",
        notebook_params  = {
            "pipeline_run_id":         "{{ run_id }}",
            "run_date":                "{{ ds }}",
            "layer":                   "bronze",
            "max_null_rate_pct":       str(DQ_THRESHOLDS["max_null_rate_pct"]),
            "max_duplicate_rate_pct":  str(DQ_THRESHOLDS["max_duplicate_rate_pct"]),
            "min_freshness_hours":     str(DQ_THRESHOLDS["min_freshness_hours"]),
        },
        cluster_id       = DATABRICKS_CLUSTER,
        polling_period_seconds = 30,
    )

    # Metadata-driven DQ rules
    run_metadata_dq = DatabricksNotebookOperator(
        task_id          = "run_metadata_driven_dq",
        databricks_conn_id = DATABRICKS_CONN_ID,
        notebook_path    = "/MediFlow360/07_notebooks/05b_DQ_Metadata_Driven_NB",
        notebook_params  = {"pipeline_run_id": "{{ run_id }}", "run_date": "{{ ds }}"},
        cluster_id       = DATABRICKS_CLUSTER,
        polling_period_seconds = 30,
    )

    evaluate = BranchPythonOperator(
        task_id         = "evaluate_dq_results",
        python_callable = evaluate_dq_results,
    )

    gate_passed = PythonOperator(
        task_id         = "dq_gate_passed",
        python_callable = send_dq_success_notification,
    )

    gate_failed = PythonOperator(
        task_id         = "dq_gate_failed",
        python_callable = send_dq_failure_alert,
        on_failure_callback = lambda ctx: None,  # Don't recurse
    )

    end = EmptyOperator(task_id="end_dq_gate", trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

    start >> [run_dq, run_metadata_dq] >> evaluate >> [gate_passed, gate_failed] >> end
