"""
MediFlow360 — Shared Airflow Hooks
Plugin: mediflow_hooks.py
Author: Priya Sharma (DE-001)
Version: 1.0

Provides:
    MediFlowTeamsHook  — Send formatted Teams adaptive card alerts
    MediFlowADFHook    — Trigger and poll Azure Data Factory pipeline runs
    MediFlowAzureMonitorHook — Push custom metrics to Azure Monitor
"""

import json
import logging
import requests
import time
from typing import Optional

from airflow.hooks.base import BaseHook

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
class MediFlowTeamsHook(BaseHook):
    """
    Hook for sending Microsoft Teams adaptive card alerts.
    Uses the Teams Incoming Webhook URL stored in an Airflow HTTP connection.

    Airflow Connection:
        conn_id:   teams_webhook
        conn_type: HTTP
        host:      <Teams webhook URL>
    """

    conn_name_attr   = "conn_id"
    default_conn_name = "teams_webhook"

    SEVERITY_COLORS = {
        "INFO":     "00B050",   # Green
        "WARNING":  "FFA500",   # Orange
        "CRITICAL": "FF0000",   # Red
    }

    def __init__(self, conn_id: str = default_conn_name):
        super().__init__()
        self.conn_id = conn_id
        self._webhook_url: Optional[str] = None

    def _get_webhook_url(self) -> str:
        if not self._webhook_url:
            conn = self.get_connection(self.conn_id)
            self._webhook_url = conn.host
        return self._webhook_url

    def send_alert(
        self,
        severity: str,
        title: str,
        message: str,
        pipeline: str,
        entity: str = None,
    ) -> bool:
        """
        Send a Teams Adaptive Card alert.
        Returns True on success, False on failure (non-blocking).
        """
        url   = self._get_webhook_url()
        color = self.SEVERITY_COLORS.get(severity.upper(), "808080")

        payload = {
            "@type":    "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary":  f"[{severity}] {title}",
            "sections": [{
                "activityTitle":    f"🔔 [{severity}] MediFlow360 | Airflow Alert",
                "activitySubtitle": f"Pipeline: {pipeline} | Entity: {entity or 'N/A'}",
                "facts": [
                    {"name": "Severity",  "value": severity},
                    {"name": "Title",     "value": title},
                    {"name": "Message",   "value": message},
                    {"name": "Pipeline",  "value": pipeline},
                    {"name": "Timestamp", "value": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())},
                ],
                "markdown": True,
            }],
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code not in (200, 202):
                log.warning("[TeamsHook] Alert failed: HTTP %s", resp.status_code)
                return False
            log.info("[TeamsHook] ✅ Alert sent: [%s] %s", severity, title)
            return True
        except Exception as e:
            log.warning("[TeamsHook] Could not send alert: %s", str(e))
            return False


# ─────────────────────────────────────────────────────────────────────────────
class MediFlowADFHook(BaseHook):
    """
    Hook for Azure Data Factory Management REST API.

    Airflow Connection:
        conn_id:   azure_data_factory
        conn_type: HTTP
        host:      management.azure.com
        login:     <service-principal-client-id>
        password:  <service-principal-client-secret>
        extra:     {"tenant_id": "...", "subscription_id": "...", "resource_group": "...", "factory_name": "..."}
    """

    conn_name_attr    = "conn_id"
    default_conn_name = "azure_data_factory"

    def __init__(self, conn_id: str = default_conn_name):
        super().__init__()
        self.conn_id = conn_id
        self._token:   Optional[str] = None
        self._sub_id:  Optional[str] = None
        self._rg:      Optional[str] = None
        self._factory: Optional[str] = None

    def _authenticate(self):
        conn       = self.get_connection(self.conn_id)
        extra      = conn.extra_dejson
        tenant_id  = extra.get("tenant_id", "")
        client_id  = conn.login
        client_secret = conn.password

        self._sub_id  = extra.get("subscription_id", "")
        self._rg      = extra.get("resource_group", "")
        self._factory = extra.get("factory_name", "")

        token_resp = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     client_id,
                "client_secret": client_secret,
                "resource":      "https://management.azure.com/",
            },
            timeout=30,
        )
        token_resp.raise_for_status()
        self._token = token_resp.json()["access_token"]

    def _headers(self) -> dict:
        if not self._token:
            self._authenticate()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def trigger_pipeline(self, pipeline_name: str, parameters: dict = None) -> str:
        """Trigger an ADF pipeline run and return the run_id."""
        if not self._token:
            self._authenticate()
        url = (
            f"https://management.azure.com/subscriptions/{self._sub_id}"
            f"/resourceGroups/{self._rg}"
            f"/providers/Microsoft.DataFactory/factories/{self._factory}"
            f"/pipelines/{pipeline_name}/createRun"
            f"?api-version=2018-06-01"
        )
        resp = requests.post(url, headers=self._headers(), json=parameters or {}, timeout=30)
        resp.raise_for_status()
        run_id = resp.json()["runId"]
        log.info("[ADFHook] Triggered %s | run_id=%s", pipeline_name, run_id)
        return run_id

    def get_pipeline_run_status(self, run_id: str) -> str:
        """Poll ADF run status. Returns: Queued | InProgress | Succeeded | Failed | Cancelled."""
        if not self._token:
            self._authenticate()
        url = (
            f"https://management.azure.com/subscriptions/{self._sub_id}"
            f"/resourceGroups/{self._rg}"
            f"/providers/Microsoft.DataFactory/factories/{self._factory}"
            f"/pipelineruns/{run_id}"
            f"?api-version=2018-06-01"
        )
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        status = resp.json().get("status", "Unknown")
        log.info("[ADFHook] run_id=%s status=%s", run_id, status)
        return status
