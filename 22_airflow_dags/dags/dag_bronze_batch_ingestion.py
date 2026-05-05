"""
MediFlow360 — Airflow DAG: Bronze Batch Ingestion
DAG ID: bronze_batch_ingestion
Schedule: 0 2 * * * (Daily at 2:00 AM IST = 20:30 UTC)
Owner: Arjun Patel (DE-002)
SLA: 3 hours from trigger

Description:
    Orchestrates the full batch ingestion pipeline for all 4 non-streaming
    source systems:
        S1 — MySQL Patients (ADF SHIR pipeline)
        S3 — SFTP Lab Results (ADF Blob Event trigger)
        S4 — CosmosDB Appointments (ADF watermark delta)
        S6 — SharePoint Staff Roster (ADF weekly full load)

    After ingestion, triggers DQ gate DAG for validation.
    All ADF pipeline runs are monitored with polling until completion.

Dependencies:
    airflow-providers-microsoft-azure  (ADF operators)
    apache-airflow-providers-http
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
import sys
import os

# Add plugins to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))
from adf_operator import ADFPipelineTriggerOperator, ADFPipelineRunSensor
from mediflow_hooks import MediFlowTeamsHook

# ─────────────────────────────────────────────────────────────────────────────
# DAG DEFAULT ARGS
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_ARGS = {
    "owner":             "arjun.patel",
    "depends_on_past":   False,
    "email":             ["priya.sharma@mrhs-de.in", "arjun.patel@mrhs-de.in"],
    "email_on_failure":  True,
    "email_on_retry":    False,
    "retries":           2,
    "retry_delay":       timedelta(minutes=10),
    "retry_exponential_backoff": True,
    "max_retry_delay":   timedelta(minutes=60),
}

# ADF resource identifiers
ADF_RESOURCE_GROUP  = "mrhs-rg-prod"
ADF_FACTORY_NAME    = "mrhs-adf-prod"
ADF_CONN_ID         = "azure_data_factory"
DATABRICKS_CONN_ID  = "databricks_default"


def on_sla_miss(dag, task_list, blocking_task_list, slas, blocking_tis):
    """SLA miss callback — sends Teams alert and logs to Azure Monitor."""
    hook = MediFlowTeamsHook(conn_id="teams_webhook")
    task_names = ", ".join([str(t) for t in task_list])
    hook.send_alert(
        severity="WARNING",
        title=f"⏰ SLA MISS: bronze_batch_ingestion",
        message=f"Tasks missed SLA: {task_names}. Check Airflow UI for details.",
        pipeline="bronze_batch_ingestion",
    )


def on_failure_callback(context):
    """Task failure callback — sends critical Teams alert."""
    hook = MediFlowTeamsHook(conn_id="teams_webhook")
    hook.send_alert(
        severity="CRITICAL",
        title=f"❌ TASK FAILED: {context['task_instance'].task_id}",
        message=(
            f"DAG: {context['dag'].dag_id} | "
            f"Task: {context['task_instance'].task_id} | "
            f"Run ID: {context['run_id']} | "
            f"Exception: {context.get('exception', 'Unknown')}"
        ),
        pipeline="bronze_batch_ingestion",
    )


def check_adf_run_status(run_id: str, conn_id: str, **kwargs):
    """Poll ADF for pipeline run completion and push result to XCom."""
    from mediflow_hooks import MediFlowADFHook
    hook = MediFlowADFHook(conn_id=conn_id)
    status = hook.get_pipeline_run_status(run_id)
    kwargs["ti"].xcom_push(key="adf_run_status", value=status)
    if status not in ["Succeeded", "Running", "Queued"]:
        raise ValueError(f"ADF pipeline failed with status: {status}")
    return status


def decide_dq_gate(**kwargs):
    """Branch: trigger DQ gate only if all upstream ingestion tasks succeeded."""
    ti = kwargs["ti"]
    statuses = [
        ti.xcom_pull(task_ids="trigger_adf_s1_patients", key="pipeline_run_id"),
        ti.xcom_pull(task_ids="trigger_adf_s3_lab",      key="pipeline_run_id"),
    ]
    # Simple check: if we have run IDs, the triggers succeeded
    if all(statuses):
        return "trigger_dq_gate"
    return "skip_dq_gate"


# ─────────────────────────────────────────────────────────────────────────────
# DAG DEFINITION
# ─────────────────────────────────────────────────────────────────────────────
with DAG(
    dag_id            = "bronze_batch_ingestion",
    description       = "MediFlow360: Daily batch ingestion for S1 MySQL, S3 SFTP, S4 CosmosDB, S6 SharePoint",
    default_args      = DEFAULT_ARGS,
    schedule_interval = "30 20 * * *",   # 20:30 UTC = 2:00 AM IST
    start_date        = datetime(2024, 1, 8),
    catchup           = False,
    max_active_runs   = 1,
    tags              = ["mediflow360", "bronze", "batch", "ingestion"],
    sla_miss_callback = on_sla_miss,
    doc_md            = """
## Bronze Batch Ingestion DAG

**Owner**: Arjun Patel (DE-002)
**Schedule**: Daily at 2:00 AM IST

### Pipeline Flow
```
S1 MySQL ──┐
S3 SFTP  ──┤→ ADF Triggers → Monitor → DQ Gate → Silver DAG trigger
S4 Cosmos──┤
S6 SharePoint──┘
```
""",
) as dag:

    # ── Start sentinel ─────────────────────────────────────────────────────────
    start = EmptyOperator(
        task_id       = "start_bronze_ingestion",
        on_failure_callback = on_failure_callback,
    )

    # ── S1: MySQL Patients (ADF Pipeline: PL_Ingest_Patients) ──────────────────
    trigger_s1 = ADFPipelineTriggerOperator(
        task_id           = "trigger_adf_s1_patients",
        adf_conn_id       = ADF_CONN_ID,
        resource_group    = ADF_RESOURCE_GROUP,
        factory_name      = ADF_FACTORY_NAME,
        pipeline_name     = "PL_Ingest_Patients",
        pipeline_parameters = {
            "source_system":    "S1_PATIENTS",
            "run_date":         "{{ ds }}",
            "pipeline_run_id":  "{{ run_id }}",
        },
        sla               = timedelta(hours=1),
        on_failure_callback = on_failure_callback,
    )

    monitor_s1 = ADFPipelineRunSensor(
        task_id           = "monitor_adf_s1_patients",
        adf_conn_id       = ADF_CONN_ID,
        resource_group    = ADF_RESOURCE_GROUP,
        factory_name      = ADF_FACTORY_NAME,
        run_id_xcom       = ("trigger_adf_s1_patients", "pipeline_run_id"),
        timeout           = 3600,    # 1-hour timeout
        poke_interval     = 60,
        on_failure_callback = on_failure_callback,
    )

    # ── S3: SFTP Lab Results (ADF Pipeline: PL_Ingest_Lab_SFTP) ───────────────
    trigger_s3 = ADFPipelineTriggerOperator(
        task_id           = "trigger_adf_s3_lab",
        adf_conn_id       = ADF_CONN_ID,
        resource_group    = ADF_RESOURCE_GROUP,
        factory_name      = ADF_FACTORY_NAME,
        pipeline_name     = "PL_Ingest_Lab_SFTP",
        pipeline_parameters = {
            "source_system":    "S3_LAB",
            "run_date":         "{{ ds }}",
            "pipeline_run_id":  "{{ run_id }}",
        },
        sla               = timedelta(hours=1, minutes=30),
        on_failure_callback = on_failure_callback,
    )

    monitor_s3 = ADFPipelineRunSensor(
        task_id           = "monitor_adf_s3_lab",
        adf_conn_id       = ADF_CONN_ID,
        resource_group    = ADF_RESOURCE_GROUP,
        factory_name      = ADF_FACTORY_NAME,
        run_id_xcom       = ("trigger_adf_s3_lab", "pipeline_run_id"),
        timeout           = 3600,
        poke_interval     = 60,
        on_failure_callback = on_failure_callback,
    )

    # ── S4: CosmosDB Appointments ──────────────────────────────────────────────
    trigger_s4 = ADFPipelineTriggerOperator(
        task_id           = "trigger_adf_s4_appointments",
        adf_conn_id       = ADF_CONN_ID,
        resource_group    = ADF_RESOURCE_GROUP,
        factory_name      = ADF_FACTORY_NAME,
        pipeline_name     = "PL_Ingest_Appointments",
        pipeline_parameters = {
            "source_system":    "S4_APPOINTMENTS",
            "run_date":         "{{ ds }}",
            "pipeline_run_id":  "{{ run_id }}",
        },
        on_failure_callback = on_failure_callback,
    )

    monitor_s4 = ADFPipelineRunSensor(
        task_id       = "monitor_adf_s4_appointments",
        adf_conn_id   = ADF_CONN_ID,
        resource_group= ADF_RESOURCE_GROUP,
        factory_name  = ADF_FACTORY_NAME,
        run_id_xcom   = ("trigger_adf_s4_appointments", "pipeline_run_id"),
        timeout       = 3600,
        poke_interval = 90,
        on_failure_callback = on_failure_callback,
    )

    # ── S6: SharePoint Staff Roster (weekly only — Monday only branch) ─────────
    def is_monday(**kwargs):
        """Only run SharePoint ingestion on Monday (weekly full-load)."""
        from datetime import datetime
        run_date = datetime.strptime(kwargs["ds"], "%Y-%m-%d")
        return "trigger_adf_s6_sharepoint" if run_date.weekday() == 0 else "skip_sharepoint"

    branch_sharepoint = BranchPythonOperator(
        task_id       = "branch_sharepoint_weekly",
        python_callable = is_monday,
    )

    trigger_s6 = ADFPipelineTriggerOperator(
        task_id           = "trigger_adf_s6_sharepoint",
        adf_conn_id       = ADF_CONN_ID,
        resource_group    = ADF_RESOURCE_GROUP,
        factory_name      = ADF_FACTORY_NAME,
        pipeline_name     = "PL_Ingest_SharePoint_Roster",
        pipeline_parameters = {"run_date": "{{ ds }}"},
        on_failure_callback = on_failure_callback,
    )

    skip_sharepoint = EmptyOperator(task_id="skip_sharepoint")

    # ── DQ Gate Trigger ────────────────────────────────────────────────────────
    branch_dq = BranchPythonOperator(
        task_id         = "branch_dq_gate",
        python_callable = decide_dq_gate,
        trigger_rule    = TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    trigger_dq = TriggerDagRunOperator(
        task_id         = "trigger_dq_gate",
        trigger_dag_id  = "data_quality_gate",
        conf            = {
            "triggered_by": "bronze_batch_ingestion",
            "run_date":     "{{ ds }}",
            "run_id":       "{{ run_id }}",
        },
        wait_for_completion = False,
    )

    skip_dq = EmptyOperator(task_id="skip_dq_gate")

    end = EmptyOperator(
        task_id      = "end_bronze_ingestion",
        trigger_rule = TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # ── DAG Dependencies ───────────────────────────────────────────────────────
    start >> [trigger_s1, trigger_s3, trigger_s4, branch_sharepoint]

    trigger_s1 >> monitor_s1
    trigger_s3 >> monitor_s3
    trigger_s4 >> monitor_s4
    branch_sharepoint >> [trigger_s6, skip_sharepoint]

    [monitor_s1, monitor_s3, monitor_s4, trigger_s6, skip_sharepoint] >> branch_dq
    branch_dq >> [trigger_dq, skip_dq]
    [trigger_dq, skip_dq] >> end
