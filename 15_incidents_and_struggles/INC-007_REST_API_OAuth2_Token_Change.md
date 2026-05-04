# Incident Report — INC-007
## Claims REST API Changed OAuth2 Token URL Without Notice
**Incident ID**: INC-007 | **Severity**: P2 — HIGH
**Detection Date**: 2024-03-25 | **Resolution Date**: 2024-03-25
**Detected by**: Suresh Kumar (OPS-001) — morning health check
**Status**: ✅ RESOLVED

---

## What Happened

At 01:00 AM IST, the ADF pipeline `PL_Ingest_Claims` ran as scheduled. The OAuth2 Web Activity that fetches the bearer token sent a POST request to `https://claims-api.insurancepartner.in/oauth/token`. The insurance partner had silently migrated their auth endpoint to `/auth/v2/token` during their 22:00–00:00 maintenance window.

The Web Activity received HTTP 301 (Redirect) but ADF's HTTP connector **does not auto-follow redirects** for POST requests. It returned an empty token. The subsequent Copy Activity ran with a blank Authorization header, received HTTP 401 from the Claims API, and ADF silently logged this as **0 records copied** — not as a failure.

Because 0 records on a quiet night was not anomalous enough to trigger ALT-007 (which needs a 20% *drop* in row count vs. previous day), **the issue went undetected for 14 hours**.

---

## Timeline

| Time | Event |
|------|--------|
| 00:00 IST | Insurance partner deploys auth migration (no notification sent) |
| 01:00 IST | PL_Ingest_Claims runs — token fetch fails silently, 0 records loaded |
| 01:05 IST | No alert fired (0 records treated as "quiet night") |
| 09:00 IST | Morning standup — nobody flags claims pipeline (no red in ADF) |
| 13:45 IST | Shobha (Billing Head) emails Sneha: *"Today's claims dashboard looks different — yesterday's numbers seem to be showing again?"* |
| 14:05 IST | Sneha pings Arjun. Arjun checks ADF — sees 0 records but green status |
| 14:20 IST | Arjun manually tests Claims API with Postman — gets 401 |
| 14:30 IST | Arjun checks insurance partner portal — finds migration notice buried in their changelog |
| 14:45 IST | Config updated in Key Vault (`claims-api-token-url`) |
| 15:00 IST | Manual re-run of PL_Ingest_Claims — successful, 847 claims loaded |
| 15:30 IST | Sneha notifies Shobha: resolved |

---

## Root Cause

1. **ADF HTTP connector does not follow POST redirects** — a known behaviour, not a bug
2. **Web Activity error handling was insufficient** — token response was not validated for content (empty string accepted as valid token)
3. **ALT-007 threshold too loose** — 0 records is a 100% drop, but it only fired if the *previous day* had records. On the specific night, the prior run had also been lighter than usual (hospital audit day, fewer procedures)

---

## Resolution

### Code Fix — Token Validation in ADF Pipeline
Added a **Set Variable activity** after the Web Activity:
```json
{
  "name": "Validate_Token",
  "type": "IfCondition",
  "expression": "@equals(length(activity('Get_OAuth_Token').output.access_token), 0)",
  "ifTrueActivities": [{
    "name": "Fail_Pipeline",
    "type": "Fail",
    "typeProperties": {
      "message": "OAuth2 token is empty. Check token URL in Key Vault: claims-api-token-url",
      "errorCode": "AUTH_TOKEN_EMPTY"
    }
  }]
}
```

### New Alert — ALT-017 (Added Post-INC-007)
| Alert ID | Trigger | Channel | Recipient |
|----------|---------|---------|-----------|
| ALT-017 | Claims ingestion = 0 records on any run | CRITICAL Teams + Email | DE-002, DE-001 |

### Process Change
- Added insurance partner contact (Rohit Sharma, rohit@insurancepartner.in) to INC escalation path
- Requested partner to add MRHS to their API change notification mailing list

---

## Lessons Learned
1. **Always validate token response content**, not just HTTP status
2. **Zero records is not always "OK"** — add an absolute zero-record alert per pipeline
3. **Third-party API changes happen without notice** — build defensive token validation

---
*MRHS Confidential | INC-007 | Closed 2024-03-25*
