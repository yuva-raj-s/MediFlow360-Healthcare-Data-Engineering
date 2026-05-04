# Databricks Notebook: 00_Helper_NB.py
# MediFlow360 — Shared Utilities, Alert Dispatcher, Audit Logger
# Author: Kavitha Rajan (DE-003) | Reviewed: Priya Sharma (DE-001)
# Version: 2.1 | Last Updated: 2024-03-10
# Usage: %run ./00_Helper_NB from any other notebook

# ============================================================
# IMPORTS
# ============================================================
import json
import hashlib
import requests
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, sha2, concat_ws,
    when, to_date, to_timestamp, trim, upper, regexp_replace
)
from pyspark.sql.types import *

# ============================================================
# CONSTANTS — Resource Names
# ============================================================
STORAGE_ACCOUNT   = "mrhsadlsprod"
CONTAINER         = "mediflow360"
ABFSS_PATH        = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net"
KEY_VAULT_SCOPE   = "mrhs-kv-scope"

# Unity Catalog Namespaces
UC_CATALOG        = "mediflow_prod"
UC_SCHEMA_BRONZE  = "bronze"
UC_SCHEMA_SILVER  = "silver"
UC_SCHEMA_GOLD    = "gold"
AUDIT_DB          = "mrhs_audit"
AUDIT_TABLE       = "pipeline_audit_log"
WATERMARK_TABLE   = "watermark_control"
SERVING_JDBC_URL  = "jdbc:sqlserver://mrhs-sqldb-prod.database.windows.net:1433;database=MediFlow360"
SYNAPSE_JDBC_URL  = "jdbc:sqlserver://mrhs-synw-prod.sql.azuresynapse.net:1433;database=mrhs-sqlpool-gold"

TEAMS_WEBHOOK_KEY = "teams-webhook-mediflow360-alerts"
EMAIL_LOGIC_APP_KEY = "logic-app-email-url"

# Alert severity levels
SEVERITY_INFO     = "INFO"
SEVERITY_WARNING  = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"


# ============================================================
# SECTION 1: KEY VAULT SECRET RETRIEVAL
# ============================================================

def get_secret(key_name: str) -> str:
    """Retrieve secret from Databricks secret scope (backed by Azure Key Vault)."""
    try:
        return dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key=key_name)
    except Exception as e:
        raise RuntimeError(f"[Helper] Failed to retrieve secret '{key_name}': {str(e)}")


# ============================================================
# SECTION 2: ADLS MOUNT MANAGEMENT
# ============================================================

def configure_adls_abfss():
    """Configure Spark to use Service Principal for direct ABFSS access."""
    try:
        tenant_id = get_secret("azure-tenant-id")
        client_id = get_secret("databricks-sp-client-id")
        client_secret = get_secret("databricks-sp-client-secret")
        
        spark.conf.set(f"fs.azure.account.auth.type.{STORAGE_ACCOUNT}.dfs.core.windows.net", "OAuth")
        spark.conf.set(f"fs.azure.account.oauth.provider.type.{STORAGE_ACCOUNT}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
        spark.conf.set(f"fs.azure.account.oauth2.client.id.{STORAGE_ACCOUNT}.dfs.core.windows.net", client_id)
        spark.conf.set(f"fs.azure.account.oauth2.client.secret.{STORAGE_ACCOUNT}.dfs.core.windows.net", client_secret)
        spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{STORAGE_ACCOUNT}.dfs.core.windows.net", f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")
        
        print(f"[Helper] ABFSS configured for {STORAGE_ACCOUNT} using Service Principal.")
    except Exception as e:
        print(f"[Helper] Warning: Could not configure ABFSS Service Principal: {str(e)}")



def get_bronze_path(source: str, date_str: str = None) -> str:
    """Returns the ABFSS Bronze layer path for a given source and optional date."""
    if date_str:
        return f"{ABFSS_PATH}/bronze/{source}/{date_str.replace('-', '/')}"
    return f"{ABFSS_PATH}/bronze/{source}"

def get_silver_table(entity: str) -> str:
    """Returns the Unity Catalog 3-level namespace for a Silver table."""
    return f"{UC_CATALOG}.{UC_SCHEMA_SILVER}.{entity}"

def get_gold_table(entity: str) -> str:
    """Returns the Unity Catalog 3-level namespace for a Gold table."""
    return f"{UC_CATALOG}.{UC_SCHEMA_GOLD}.{entity}"


# ============================================================
# SECTION 3: WATERMARK MANAGEMENT
# ============================================================

def get_watermark(entity_name: str) -> str:
    """
    Read the last processed watermark for an entity from Azure SQL watermark_control table.
    Returns ISO timestamp string. Returns '1900-01-01 00:00:00' if no record exists.
    """
    jdbc_url = SERVING_JDBC_URL
    jdbc_pwd = get_secret("azuresql-password")
    try:
        wm_df = spark.read.format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", f"bronze_meta.{WATERMARK_TABLE}") \
            .option("user", "adf_reader") \
            .option("password", jdbc_pwd) \
            .load() \
            .filter(col("entity_name") == entity_name) \
            .select("last_watermark_value")

        if wm_df.count() == 0:
            print(f"[Helper] No watermark found for '{entity_name}'. Using default: 1900-01-01")
            return "1900-01-01 00:00:00"

        return wm_df.collect()[0]["last_watermark_value"]
    except Exception as e:
        send_alert(
            severity=SEVERITY_WARNING,
            title="Watermark Read Failure",
            message=f"Could not read watermark for entity '{entity_name}': {str(e)}",
            pipeline="Helper_NB"
        )
        return "1900-01-01 00:00:00"


def update_watermark(entity_name: str, new_watermark: str, pipeline_run_id: str):
    """
    Update watermark for an entity in Azure SQL watermark_control table.
    Uses MERGE to upsert.
    """
    jdbc_url = SERVING_JDBC_URL
    jdbc_pwd = get_secret("azuresql-password")

    update_df = spark.createDataFrame(
        [(entity_name, new_watermark, datetime.now(timezone.utc).isoformat(), pipeline_run_id)],
        ["entity_name", "last_watermark_value", "updated_at", "last_pipeline_run_id"]
    )
    update_df.write.format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "bronze_meta.watermark_staging") \
        .option("user", "adf_reader") \
        .option("password", jdbc_pwd) \
        .mode("overwrite") \
        .save()

    # Execute MERGE via stored procedure
    conn_properties = {"user": "adf_reader", "password": jdbc_pwd, "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"}
    print(f"[Helper] Watermark updated for '{entity_name}' → {new_watermark}")


# ============================================================
# SECTION 4: AUDIT LOGGING
# ============================================================

def write_audit_log(
    pipeline_name: str,
    notebook_name: str,
    run_id: str,
    source_system: str,
    entity_name: str,
    records_read: int,
    records_written: int,
    records_rejected: int,
    status: str,                   # SUCCESS | FAILED | PARTIAL
    start_time: datetime,
    end_time: datetime,
    error_message: str = None
):
    """
    Write immutable audit record to mrhs_audit.pipeline_audit_log.
    This table has no UPDATE/DELETE permissions — append only.
    """
    jdbc_url = SERVING_JDBC_URL
    jdbc_pwd = get_secret("azuresql-password")

    duration_seconds = int((end_time - start_time).total_seconds())

    audit_data = [(
        pipeline_name, notebook_name, run_id, source_system, entity_name,
        records_read, records_written, records_rejected,
        status, start_time.isoformat(), end_time.isoformat(),
        duration_seconds, error_message or ""
    )]

    audit_schema = StructType([
        StructField("pipeline_name", StringType()),
        StructField("notebook_name", StringType()),
        StructField("run_id", StringType()),
        StructField("source_system", StringType()),
        StructField("entity_name", StringType()),
        StructField("records_read", IntegerType()),
        StructField("records_written", IntegerType()),
        StructField("records_rejected", IntegerType()),
        StructField("status", StringType()),
        StructField("start_time", StringType()),
        StructField("end_time", StringType()),
        StructField("duration_seconds", IntegerType()),
        StructField("error_message", StringType()),
    ])

    audit_df = spark.createDataFrame(audit_data, schema=audit_schema)
    audit_df.write.format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"{AUDIT_DB}.{AUDIT_TABLE}") \
        .option("user", "adf_reader") \
        .option("password", jdbc_pwd) \
        .mode("append") \
        .save()

    print(f"[Helper] Audit log written: {status} | {records_written} records | {duration_seconds}s")


# ============================================================
# SECTION 5: ALERT DISPATCHER
# ============================================================

def send_alert(severity: str, title: str, message: str, pipeline: str, entity: str = None):
    """
    Send alert to Microsoft Teams webhook and/or Logic Apps email endpoint.
    severity: INFO | WARNING | CRITICAL
    """
    color_map = {
        SEVERITY_INFO:     "00B050",   # Green
        SEVERITY_WARNING:  "FFA500",   # Orange
        SEVERITY_CRITICAL: "FF0000",   # Red
    }

    card_color = color_map.get(severity, "808080")
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Teams Adaptive Card payload
    teams_payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": card_color,
        "summary": f"[{severity}] {title}",
        "sections": [{
            "activityTitle": f"🚨 [{severity}] MediFlow360 Alert",
            "activitySubtitle": f"Pipeline: {pipeline} | Entity: {entity or 'N/A'}",
            "facts": [
                {"name": "Alert Title", "value": title},
                {"name": "Message",     "value": message},
                {"name": "Severity",    "value": severity},
                {"name": "Timestamp",   "value": timestamp_str},
                {"name": "Pipeline",    "value": pipeline},
            ],
            "markdown": True
        }]
    }

    try:
        webhook_url = get_secret(TEAMS_WEBHOOK_KEY)
        response = requests.post(webhook_url, json=teams_payload, timeout=10)
        if response.status_code not in [200, 202]:
            print(f"[Helper] Teams alert failed: HTTP {response.status_code}")
        else:
            print(f"[Helper] Teams alert sent: [{severity}] {title}")
    except Exception as e:
        print(f"[Helper] WARNING: Could not send Teams alert: {str(e)}")

    # For CRITICAL alerts — also trigger email via Logic App
    if severity == SEVERITY_CRITICAL:
        try:
            email_url = get_secret(EMAIL_LOGIC_APP_KEY)
            email_payload = {
                "subject": f"[CRITICAL] MediFlow360: {title}",
                "body": f"<b>Pipeline</b>: {pipeline}<br><b>Entity</b>: {entity}<br><b>Message</b>: {message}<br><b>Time</b>: {timestamp_str}",
                "to": "priya.sharma@mrhs-de.in;sneha.iyer@mrhs-de.in;cio@mrhs.in"
            }
            requests.post(email_url, json=email_payload, timeout=10)
            print(f"[Helper] Critical email alert dispatched.")
        except Exception as e:
            print(f"[Helper] WARNING: Could not send email alert: {str(e)}")


# ============================================================
# SECTION 6: DATA QUALITY UTILITIES
# ============================================================

def check_null_rate(df, column_name: str, threshold_pct: float = 5.0) -> dict:
    """Check null rate for a column. Returns dict with result and triggers alert if above threshold."""
    total = df.count()
    nulls = df.filter(col(column_name).isNull()).count()
    null_rate = (nulls / total * 100) if total > 0 else 0.0

    result = {
        "column": column_name,
        "total_records": total,
        "null_count": nulls,
        "null_rate_pct": round(null_rate, 2),
        "passed": null_rate <= threshold_pct
    }

    if not result["passed"]:
        send_alert(
            severity=SEVERITY_WARNING,
            title=f"High Null Rate: {column_name}",
            message=f"Null rate {null_rate:.1f}% exceeds threshold {threshold_pct}% in column '{column_name}'",
            pipeline="Data_Quality_NB"
        )
    return result


def compute_record_hash(df, columns: list, hash_col_name: str = "record_hash"):
    """Compute SHA-256 hash of specified columns for SCD-2 change detection."""
    return df.withColumn(
        hash_col_name,
        sha2(concat_ws("|", *[col(c).cast(StringType()) for c in columns]), 256)
    )


def mask_aadhaar(df, raw_col: str = "aadhaar_number", hashed_col: str = "aadhaar_hash"):
    """Hash Aadhaar number using SHA-256. Remove raw column."""
    return df \
        .withColumn(hashed_col, sha2(col(raw_col).cast(StringType()), 256)) \
        .drop(raw_col)


def mask_phone(df, col_name: str = "phone_number"):
    """Mask first 6 digits of phone number: XXXXXX1234."""
    return df.withColumn(
        col_name,
        regexp_replace(col(col_name), r"^\d{6}", "XXXXXX")
    )


# ============================================================
# SECTION 7: SPARK SESSION SETUP
# ============================================================

def get_spark():
    """Return active Spark session or create one."""
    return SparkSession.builder \
        .appName("MediFlow360") \
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
        .getOrCreate()


# ============================================================
# SELF-CHECK (runs on %run invocation)
# ============================================================

print("=" * 60)
print("  MediFlow360 | 00_Helper_NB | v2.1")
print("=" * 60)

spark = get_spark()
print(f"✅ Spark version: {spark.version}")

try:
    configure_adls_abfss()
    print("✅ ABFSS config: OK")
except Exception as e:
    print(f"⚠️  ABFSS config: FAILED — {str(e)}")

try:
    _ = get_secret("adls-account-key")
    print("✅ Key Vault (scope): OK")
except Exception as e:
    print(f"⚠️  Key Vault: FAILED — {str(e)}")

print("=" * 60)
print("  Helper_NB ready. All utilities available.")
print("=" * 60)
