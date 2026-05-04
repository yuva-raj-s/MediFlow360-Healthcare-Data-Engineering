# Alert Architecture
## MediFlow360 — Full Alerting Stack Design
**Document ID**: MRHS-ALT-001 | **Version**: 1.2 | **Author**: Suresh Kumar (OPS-001)
**Reviewed by**: Priya Sharma (DE-001), Vikram Krishnan (SA-001)

---

## Alert Stack Overview

```
[Trigger Source]
     ↓
Azure Monitor Metric Alert / ADF Diagnostic Alert / Custom Python (Helper_NB)
     ↓
Azure Monitor Action Group (mrhs-ag-primary)
     ↓
     ├── Logic App: mrhs-la-email-alert  →  Outlook 365 Email
     └── Logic App: mrhs-la-teams-alert →  Teams Webhook → #mediflow360-alerts
```

---

## Alert Rules — Complete List (16 Rules)

### Category 1: Pipeline Health

| Alert ID | Name | Trigger Condition | Severity | Recipients |
|----------|------|-------------------|----------|------------|
| ALT-001 | ADF Pipeline Failure | Any ADF pipeline Run Status = Failed | CRITICAL | DE-001, OPS-001 + Teams |
| ALT-002 | Pipeline Runtime > 60 min | ADF pipeline duration > 3600s | WARNING | DE-001 |
| ALT-003 | Databricks Cluster Crash | Cluster terminated unexpectedly | CRITICAL | DE-001, DE-002, DE-003 |
| ALT-004 | Dashboard Refresh Failed | Power BI dataset refresh failure event | CRITICAL | PM-001, DA-001, CIO |
| ALT-005 | ADLS Storage > 80% | Storage account used capacity > 4GB (80% of 5GB free) | WARNING | OPS-001, DG-001 |

### Category 2: Data Quality

| Alert ID | Name | Trigger Condition | Severity | Recipients |
|----------|------|-------------------|----------|------------|
| ALT-006 | High Null Rate | Null rate > 5% in critical field (DOB, patient_id, claim_id) | WARNING | DE-001, DA-001 |
| ALT-007 | Row Count Drop | Silver/Bronze row count drops > 20% vs previous day | CRITICAL | DE-001, PM-001 |
| ALT-007b | Silver/Bronze Count Ratio | Silver patient count > 1.5× Bronze count (INC-005 fix) | WARNING | DE-001, DE-003 |
| ALT-008 | Duplicate Patient IDs | Duplicate global_patient_id in silver.dim_patient is_current=1 | CRITICAL | DG-001, DE-001 |
| ALT-009 | Schema Drift Detected | Bronze schema columns changed vs registered schema | WARNING | DE-002, SA-001 |
| ALT-010 | PII in Gold Layer | PII column name detected in /gold/ path writes | CRITICAL | DG-001, CIO + Email |

### Category 3: Business KPI

| Alert ID | Name | Trigger Condition | Severity | Recipients |
|----------|------|-------------------|----------|------------|
| ALT-011 | High Readmission Rate | 30-day readmission rate > 5% (weekly check) | WARNING | CMO (Dr. Meena) |
| ALT-012 | Claims Denial Rate Breach | Denial rate > 8% (weekly check) | WARNING | CFO, Billing Head (Shobha) |
| ALT-013 | Critical Lab Value | Lab result flagged is_critical_flag = 1 | CRITICAL | Lab Head (Kaveri), on-duty doctor |
| ALT-014 | Drug Stockout Predicted | current_stock < avg_daily_consumption × 7 | WARNING | Pharmacy Head (Rajan) |
| ALT-015 | Fraud Pattern Detected | Fraud score ≥ 5 on any claim | CRITICAL | CFO (Balaji), Billing Head (Shobha) |
| ALT-016 | ICU Capacity Critical | ICU bed occupancy > 90% at any hospital | CRITICAL | Cardiology Head (Dr. Anil), CMO |

---

## Implementation Details

### Azure Monitor Action Group Setup

**Action Group Name**: `mrhs-ag-primary`
**Resource Group**: `mrhs-rg-mediflow360`

Actions:
- Email: `de-team@mrhs-de.in` (DE-001, DE-002, DE-003, OPS-001)
- Logic App: `mrhs-la-teams-alert` (Teams webhook POST)
- Logic App: `mrhs-la-email-alert` (Stakeholder email for business alerts)

### ADF Diagnostic Settings

Enable for ADF `mrhs-adf-prod`:
```
Log Categories: PipelineRuns, ActivityRuns, TriggerRuns
Destination: Log Analytics Workspace (mrhs-law-prod)
Retention: 30 days
```

Create Azure Monitor Alert Rule:
- Signal: `PipelineFailedRuns` metric
- Threshold: Count > 0
- Evaluation period: 5 minutes
- Action Group: `mrhs-ag-primary`

### Teams Webhook (Logic App: mrhs-la-teams-alert)

Trigger: HTTP POST
Connector: Microsoft Teams → Post a message to channel
Channel: `#mediflow360-alerts`
Workspace: `MRHS Data Platform`

Sample Teams card payload (from Helper_NB.py):
```json
{
  "@type": "MessageCard",
  "themeColor": "FF0000",
  "summary": "[CRITICAL] ADF Pipeline Failure",
  "sections": [{
    "activityTitle": "🚨 [CRITICAL] MediFlow360 Alert",
    "facts": [
      {"name": "Alert", "value": "PL_Ingest_Patients FAILED"},
      {"name": "Time",  "value": "2024-03-14 01:23 UTC"},
      {"name": "Run ID","value": "abc-123-def-456"}
    ]
  }]
}
```

### Email Alert via Logic App (mrhs-la-email-alert)

For CRITICAL severity only. Recipients:
- Pipeline alerts → DE-001, OPS-001
- Business KPI alerts → respective stakeholder (from RECIPIENTS map in Helper_NB)
- PII exposure (ALT-010) → DG-001, CIO (always)

---

## Alert Escalation Policy

| Time Since Alert | Action |
|-----------------|--------|
| 0 min | Automated Teams + Email sent |
| 15 min (unacknowledged) | DE-001 phones OPS-001 directly |
| 30 min (unresolved) | PM-001 + SA-001 looped in |
| 2 hrs (unresolved, business impact) | CIO briefed via email |
| 4 hrs (critical data breach) | CEO notified, Incident declared P1 |

---

## On-Call Schedule (Current Sprint)

| Week | Primary | Backup |
|------|---------|--------|
| Jan 22–Feb 2 | OPS-001 (Suresh) | DE-002 (Arjun) |
| Feb 5–Feb 16 | DE-001 (Priya) | OPS-001 (Suresh) |
| Feb 19–Mar 1 | DE-002 (Arjun) | DE-003 (Kavitha) |
| Mar 4–Mar 15 | DE-003 (Kavitha) | DE-001 (Priya) |

---
*MRHS Confidential | Alert Architecture | v1.2*
