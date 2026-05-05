"""
MediFlow360 — Custom Airflow Operator: Databricks Notebook Runner
Plugin: databricks_operator.py
Author: Priya Sharma (DE-001)
Version: 1.0

Description:
    Custom Airflow operator that triggers a Databricks notebook run via
    the Databricks Jobs API (REST v2.1) and polls until completion.
    Supports both existing cluster and new cluster job runs.

    This operator is preferred over the official DatabricksRunNowOperator
    for MediFlow360 because it:
    1. Supports run_name with template for unique Airflow run ID tracking
    2. Logs notebook output to Airflow XCom
    3. Integrates with MediFlow360 Teams alerting on failure
"""

import time
import json
import logging
from datetime import timedelta
from typing import Optional

import requests
from airflow.models import BaseOperator
from airflow.sensors.base import BaseSensorOperator
from airflow.hooks.base import BaseHook
from airflow.utils.decorators import apply_defaults

log = logging.getLogger(__name__)


class DatabricksHook(BaseHook):
    """Hook for Databricks REST API 2.1."""

    conn_name_attr = "databricks_conn_id"
    default_conn_name = "databricks_default"
    hook_name = "Databricks"

    def __init__(self, databricks_conn_id: str = default_conn_name):
        super().__init__()
        self.databricks_conn_id = databricks_conn_id
        self._base_url: Optional[str] = None
        self._token:    Optional[str] = None

    def _get_connection(self):
        conn = self.get_connection(self.databricks_conn_id)
        self._base_url = conn.host.rstrip("/")
        self._token    = conn.password or conn.extra_dejson.get("token", "")

    def _headers(self) -> dict:
        if not self._token:
            self._get_connection()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def submit_run(self, run_config: dict) -> str:
        """Submit a one-time run and return the run_id."""
        if not self._base_url:
            self._get_connection()
        resp = requests.post(
            f"{self._base_url}/api/2.1/jobs/runs/submit",
            headers=self._headers(),
            json=run_config,
            timeout=30,
        )
        resp.raise_for_status()
        run_id = str(resp.json()["run_id"])
        log.info("[DatabricksHook] Run submitted. run_id=%s", run_id)
        return run_id

    def get_run_state(self, run_id: str) -> dict:
        """Get current state of a run."""
        if not self._base_url:
            self._get_connection()
        resp = requests.get(
            f"{self._base_url}/api/2.1/jobs/runs/get",
            headers=self._headers(),
            params={"run_id": run_id},
            timeout=30,
        )
        resp.raise_for_status()
        data  = resp.json()
        state = data.get("state", {})
        return {
            "life_cycle_state":  state.get("life_cycle_state", "UNKNOWN"),
            "result_state":      state.get("result_state", ""),
            "state_message":     state.get("state_message", ""),
            "notebook_output":   data.get("notebook_output", {}).get("result", ""),
            "run_page_url":      data.get("run_page_url", ""),
        }

    def cancel_run(self, run_id: str):
        """Cancel a running job."""
        if not self._base_url:
            self._get_connection()
        requests.post(
            f"{self._base_url}/api/2.1/jobs/runs/cancel",
            headers=self._headers(),
            json={"run_id": int(run_id)},
            timeout=30,
        )


class DatabricksNotebookOperator(BaseOperator):
    """
    Runs a Databricks notebook as a one-time run via the Jobs API.

    :param notebook_path:    Absolute path to the notebook in Databricks workspace.
    :param notebook_params:  Dict of widget parameters to pass to the notebook.
    :param cluster_id:       ID of an existing all-purpose cluster to attach to.
    :param new_cluster:      Dict defining a new cluster (if cluster_id is None).
    :param polling_period_seconds: How often to poll for run completion.
    :param databricks_conn_id: Airflow connection ID for Databricks.
    """

    template_fields = ("notebook_params",)
    ui_color = "#e34c26"   # Databricks orange

    @apply_defaults
    def __init__(
        self,
        notebook_path: str,
        notebook_params: dict = None,
        cluster_id: str = None,
        new_cluster: dict = None,
        polling_period_seconds: int = 30,
        databricks_conn_id: str = "databricks_default",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.notebook_path           = notebook_path
        self.notebook_params         = notebook_params or {}
        self.cluster_id              = cluster_id
        self.new_cluster             = new_cluster
        self.polling_period_seconds  = polling_period_seconds
        self.databricks_conn_id      = databricks_conn_id
        self._run_id: Optional[str]  = None

    def execute(self, context):
        hook = DatabricksHook(self.databricks_conn_id)

        run_config = {
            "run_name": f"mediflow360_{self.task_id}_{context['run_id']}",
            "notebook_task": {
                "notebook_path": self.notebook_path,
                "base_parameters": {k: str(v) for k, v in self.notebook_params.items()},
                "source": "WORKSPACE",
            },
        }

        if self.cluster_id:
            run_config["existing_cluster_id"] = self.cluster_id
        elif self.new_cluster:
            run_config["new_cluster"] = self.new_cluster
        else:
            raise ValueError("Either cluster_id or new_cluster must be provided.")

        self._run_id = hook.submit_run(run_config)
        context["ti"].xcom_push(key="databricks_run_id", value=self._run_id)
        log.info("[DatabricksNotebookOperator] Run submitted: run_id=%s", self._run_id)

        # Poll until terminal state
        while True:
            state = hook.get_run_state(self._run_id)
            life_cycle  = state["life_cycle_state"]
            result      = state["result_state"]
            message     = state["state_message"]
            url         = state["run_page_url"]

            log.info(
                "[Databricks] run_id=%s | state=%s | result=%s | msg=%s",
                self._run_id, life_cycle, result, message
            )

            if life_cycle == "TERMINATED":
                if result == "SUCCESS":
                    log.info("[Databricks] ✅ Notebook succeeded. URL: %s", url)
                    context["ti"].xcom_push(key="notebook_output", value=state["notebook_output"])
                    return self._run_id
                else:
                    raise RuntimeError(
                        f"Databricks run FAILED: run_id={self._run_id}, "
                        f"result={result}, message={message}, url={url}"
                    )
            elif life_cycle in ("INTERNAL_ERROR", "SKIPPED"):
                raise RuntimeError(
                    f"Databricks run error: state={life_cycle}, message={message}"
                )

            time.sleep(self.polling_period_seconds)

    def on_kill(self):
        """Cancel the Databricks run if Airflow task is killed."""
        if self._run_id:
            hook = DatabricksHook(self.databricks_conn_id)
            hook.cancel_run(self._run_id)
            log.info("[DatabricksNotebookOperator] Cancelled run: %s", self._run_id)


class DatabricksRunSensor(BaseSensorOperator):
    """
    Sensor that pokes a Databricks run until it reaches a terminal state.
    Use this when you want to submit a run in one task and wait in another.
    """

    @apply_defaults
    def __init__(
        self,
        run_id_xcom: tuple,   # (task_id, xcom_key)
        databricks_conn_id: str = "databricks_default",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.run_id_xcom        = run_id_xcom
        self.databricks_conn_id = databricks_conn_id

    def poke(self, context):
        run_id = context["ti"].xcom_pull(task_ids=self.run_id_xcom[0], key=self.run_id_xcom[1])
        if not run_id:
            log.warning("[DatabricksRunSensor] No run_id found in XCom.")
            return False

        hook  = DatabricksHook(self.databricks_conn_id)
        state = hook.get_run_state(run_id)
        life  = state["life_cycle_state"]
        log.info("[DatabricksRunSensor] run_id=%s state=%s", run_id, life)

        if life == "TERMINATED":
            if state["result_state"] == "SUCCESS":
                return True
            raise RuntimeError(f"Databricks run failed: {state}")
        return False
