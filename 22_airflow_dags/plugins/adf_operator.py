"""
MediFlow360 — Custom Airflow Operator: ADF Pipeline Trigger & Sensor
Plugin: adf_operator.py
Author: Arjun Patel (DE-002)
Version: 1.0

Provides:
    ADFPipelineTriggerOperator — Triggers an ADF pipeline run and pushes run_id to XCom
    ADFPipelineRunSensor       — Pokes ADF until run reaches terminal state
"""

import time
import logging
from typing import Optional, Tuple

from airflow.models import BaseOperator
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults

log = logging.getLogger(__name__)

TERMINAL_STATES  = {"Succeeded", "Failed", "Cancelled"}
SUCCESS_STATES   = {"Succeeded"}


class ADFPipelineTriggerOperator(BaseOperator):
    """
    Triggers an Azure Data Factory pipeline run.
    Pushes the ADF run_id to XCom for downstream sensor/monitoring tasks.

    :param adf_conn_id:        Airflow connection ID for Azure Data Factory.
    :param resource_group:     Azure resource group containing the factory.
    :param factory_name:       ADF factory name.
    :param pipeline_name:      Name of the ADF pipeline to trigger.
    :param pipeline_parameters: Dict of parameters to pass to the pipeline run.
    """

    template_fields = ("pipeline_parameters",)
    ui_color = "#0078d4"   # Azure blue

    @apply_defaults
    def __init__(
        self,
        adf_conn_id: str,
        resource_group: str,
        factory_name: str,
        pipeline_name: str,
        pipeline_parameters: dict = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.adf_conn_id          = adf_conn_id
        self.resource_group       = resource_group
        self.factory_name         = factory_name
        self.pipeline_name        = pipeline_name
        self.pipeline_parameters  = pipeline_parameters or {}

    def execute(self, context):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from mediflow_hooks import MediFlowADFHook

        hook = MediFlowADFHook(conn_id=self.adf_conn_id)

        # Inject Airflow run_id into ADF parameters for end-to-end lineage
        params = dict(self.pipeline_parameters)
        params["airflow_run_id"]  = context["run_id"]
        params["airflow_dag_id"]  = context["dag"].dag_id
        params["airflow_task_id"] = self.task_id

        run_id = hook.trigger_pipeline(self.pipeline_name, params)
        context["ti"].xcom_push(key="pipeline_run_id", value=run_id)

        log.info(
            "[ADFTrigger] ✅ Pipeline '%s' triggered | ADF run_id=%s",
            self.pipeline_name, run_id,
        )
        return run_id


class ADFPipelineRunSensor(BaseSensorOperator):
    """
    Sensor that polls an ADF pipeline run until it reaches a terminal state.

    :param adf_conn_id:    Airflow connection ID.
    :param resource_group: Azure resource group.
    :param factory_name:   ADF factory name.
    :param run_id_xcom:    Tuple of (task_id, xcom_key) to retrieve the ADF run_id.
    :param timeout:        Max polling time in seconds.
    :param poke_interval:  Seconds between polls.
    """

    @apply_defaults
    def __init__(
        self,
        adf_conn_id: str,
        resource_group: str,
        factory_name: str,
        run_id_xcom: Tuple[str, str],
        timeout: int = 3600,
        poke_interval: int = 60,
        **kwargs,
    ):
        super().__init__(
            timeout=timeout,
            poke_interval=poke_interval,
            mode="reschedule",
            **kwargs,
        )
        self.adf_conn_id   = adf_conn_id
        self.resource_group = resource_group
        self.factory_name  = factory_name
        self.run_id_xcom   = run_id_xcom

    def poke(self, context) -> bool:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from mediflow_hooks import MediFlowADFHook

        run_id = context["ti"].xcom_pull(
            task_ids=self.run_id_xcom[0],
            key=self.run_id_xcom[1],
        )

        if not run_id:
            log.warning("[ADFSensor] No run_id found in XCom for %s.", self.run_id_xcom)
            return False

        hook   = MediFlowADFHook(conn_id=self.adf_conn_id)
        status = hook.get_pipeline_run_status(run_id)

        log.info("[ADFSensor] ADF run_id=%s | status=%s", run_id, status)

        if status in TERMINAL_STATES:
            if status in SUCCESS_STATES:
                log.info("[ADFSensor] ✅ ADF pipeline succeeded.")
                return True
            else:
                raise RuntimeError(
                    f"ADF pipeline run failed: run_id={run_id}, status={status}"
                )

        return False  # Still running — poke again later
