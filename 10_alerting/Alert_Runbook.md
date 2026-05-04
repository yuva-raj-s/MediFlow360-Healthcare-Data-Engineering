# Alert Response Runbook
## MediFlow360
**Document ID**: MRHS-OPS-002

### ALT-001: ADF Pipeline Failure
**Severity**: CRITICAL
1. Check ADF Monitor tab. Identify failed activity.
2. If `Copy Data` failed, check source system connection (SHIR status).
3. If Databricks Notebook failed, click the `runPageUrl` to view cluster logs.
4. Escalate to DE-002 (ADF) or DE-003 (Databricks).

### ALT-005: ADLS Storage > 80%
**Severity**: WARNING
1. Free tier is 5GB.
2. Run `Vacuum` command on Delta/Parquet tables.
3. Check `/archive/` folder for files older than 30 days and delete.

### ALT-010: PII in Gold Layer
**Severity**: CRITICAL
1. Immediate action: Revoke Power BI access to Gold layer.
2. Delete the offending parquet files.
3. Notify Compliance Officer (Ms. Preethi).