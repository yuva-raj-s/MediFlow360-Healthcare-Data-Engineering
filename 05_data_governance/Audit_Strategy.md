# Audit Logging Strategy
**Document ID**: MRHS-DG-004

### Pipeline Execution Audit
Every pipeline run logs an immutable record to `mrhs_audit.pipeline_audit_log` in Azure SQL.
**Columns**: `pipeline_name`, `notebook_name`, `run_id`, `records_read`, `records_written`, `status`, `duration_seconds`.
**Immutability**: Azure SQL enforces `DENY UPDATE, DELETE ON mrhs_audit.pipeline_audit_log TO PUBLIC`.

### Data Access Audit
- ADLS Gen2 Diagnostic Settings route all Read/Write events to Log Analytics workspace.
- Azure SQL Auditing routes all queries to Log Analytics.

### Fraud Flag Audit
- CFO requirement (BR-006): Any claim scoring >= 5 is logged to `gold.fraud_flags`.
- False positives are marked via an internal app, creating a feedback loop for Phase 2 ML.