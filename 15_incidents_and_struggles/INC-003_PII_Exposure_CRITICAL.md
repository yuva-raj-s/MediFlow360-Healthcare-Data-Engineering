# Incident Report — INC-003
## PII Exposure in Gold Layer — Aadhaar Numbers Accessible
**Incident ID**: INC-003 | **Severity**: P1 — CRITICAL 🔴
**Detection Date**: 2024-02-28 | **Resolution Date**: 2024-03-01
**Detected by**: DG-001 Lakshmi Venkat (routine audit query)
**Reported to**: CIO (Ms. Divya Anand), Compliance Officer (Ms. Preethi Nair)
**Status**: ✅ RESOLVED + Compliance Memo Filed

---

## What Happened

Mohammed Farhan (DE-004, Junior DE) was debugging a discrepancy in patient count between the Silver layer and a manual Excel count shared by the billing team. He ran an exploratory ad-hoc query in Databricks and inadvertently created a **temporary cached DataFrame** that included the `aadhaar_hash` column from Silver AND cross-joined it with a reference table that contained the actual Aadhaar suffixes (last 4 digits kept for matching).

He then wrote this cached result to the Gold layer's `/gold/debug/` folder (which he thought was temporary) to share with Arjun for comparison.

The `/gold/debug/` folder was accessible to DA-001 (Rahul) and had no PII access restriction. Rahul's Power BI gateway had read access to all of `/gold/`.

Lakshmi (DG-001) discovered this 3 days later during her monthly data access audit by noticing an unexpected folder in `/gold/` with schema containing `aadhaar_last4`.

---

## Timeline

| Time | Event |
|------|-------|
| 2024-02-25 16:30 | Farhan creates debug parquet in /gold/debug/ |
| 2024-02-28 14:00 | Lakshmi's monthly audit scan detects PII in /gold/debug/ |
| 2024-02-28 14:15 | Lakshmi immediately flags to Priya and DG escalation path |
| 2024-02-28 14:20 | Alert ALT-010 triggered (PII in non-masked layer) → CIO + Compliance notified |
| 2024-02-28 14:30 | Debug folder access revoked by OPS-001 (Suresh) |
| 2024-02-28 14:35 | Priya confirms file deleted from ADLS |
| 2024-02-28 15:00 | Compliance Officer (Ms. Preethi) joins call |
| 2024-02-28 16:00 | CIO briefed; decision: file DPDP internal incident report |
| 2024-03-01 09:00 | Full audit of all /gold/ subfolders completed — no other PII found |
| 2024-03-01 12:00 | Compliance memo filed; Farhan counselled |
| 2024-03-01 15:00 | Access control changes deployed |

---

## Root Cause

1. **No access control on /gold/debug/** — folder was writable by any team member
2. **No automated PII scan** on Gold layer writes
3. Junior engineer not aware that aadhaar_last4 (even partial) is still considered PII under DPDP Act 2023
4. No guard-rail preventing writing to /gold/ outside of official Gold_NB notebook

---

## Data Exposure Assessment

- **Data exposed**: aadhaar_last4 field for ~18,000 patient records
- **Who accessed it**: Rahul's Power BI gateway service principal had read access to /gold/ — but no query was ever executed on that folder from Power BI (confirmed via ADLS access logs)
- **External exposure**: NONE confirmed — data was internal-only, accessed only during ingestion window
- **DPDP Impact**: Near-miss; per legal review, no mandatory regulator notification required as no external party accessed the data

---

## Resolution

### Immediate Actions
1. Deleted `/gold/debug/` folder (confirmed by ADLS access log)
2. Revoked write access to `/gold/` for DE-004 role
3. All team members briefed on PII classification (Aadhaar partial counts as PII)

### Access Control Changes (OPS-001)
```
/gold/          → Write: Gold_NB service principal ONLY; Read: Analysts + gateway
/gold/debug/    → DELETED (folder removed)
/silver/        → Write: Silver_NB + SCD2_NB service principals ONLY
/bronze/        → Write: Bronze_NB service principal + ADF; Read: DE team
```

### Process Changes (DG-001)
- Added automated PII column scan to `05_Data_Quality_NB.py`:
  ```python
  PII_COLUMNS = ["aadhaar", "phone", "dob", "address", "name"]
  # Scan Gold output for any column matching PII_COLUMNS names
  # If found → CRITICAL alert ALT-010 + block write
  ```
- Gold_NB must now pass PII scan before writing; any failure raises exception
- Monthly data access audit moved to weekly for 3 months

---

## Compliance Memo Summary

**To**: CIO (Ms. Divya Anand), Compliance Officer (Ms. Preethi Nair)
**From**: Lakshmi Venkat (DG-001)
**Date**: 2024-03-01
**Subject**: INC-003 DPDP Compliance Assessment

After review, this incident is classified as a **near-miss data incident** under DPDP Act 2023. Key findings:
- PII (partial Aadhaar) was written to an unrestricted internal storage layer
- No external or unauthorized party accessed the data (confirmed via logs)
- DPDP Act Section 8(6) mandatory breach notification threshold NOT met
- However, MRHS internal Data Governance Policy Section 4.2 was violated

**Recommended actions (completed)**:
1. Automated PII scanning gate on Gold layer writes ✅
2. Access control tightening on ADLS layers ✅
3. DE-004 PII awareness training ✅
4. Updated `05_data_governance/PII_Classification_Matrix.md` to explicitly list partial Aadhaar ✅

---
*MRHS Confidential | INC-003 Incident Report | Closed 2024-03-01*
