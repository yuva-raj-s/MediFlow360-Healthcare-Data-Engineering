# Incident Report — INC-005
## SCD Type 2 Broke the Incremental Watermark Logic
**Incident ID**: INC-005 | **Severity**: P2 — HIGH
**Detection Date**: 2024-03-14 | **Resolution Date**: 2024-03-16
**Detected by**: Rahul Nair (DA-001) | **Resolved by**: Kavitha Rajan (DE-003), Priya Sharma (DE-001)
**Status**: ✅ RESOLVED

---

## Timeline

| Time | Event |
|------|-------|
| 2024-03-14 08:12 | Rahul opens Power BI dashboard for morning review |
| 2024-03-14 08:15 | Notices patient count: **54,218** (was 18,400 yesterday) |
| 2024-03-14 08:17 | Posts in #mediflow360-dev |
| 2024-03-14 08:19 | Arjun responds: *"guys the patient count just tripled 💀 something is very wrong"* |
| 2024-03-14 08:22 | Priya: *"@Kavitha drop everything. @Farhan pull the audit logs NOW"* |
| 2024-03-14 08:45 | Farhan pulls pipeline audit log — Bronze_NB ran fine, 423 records |
| 2024-03-14 09:10 | Kavitha identifies SCD-2 notebook ran 3× due to watermark issue |
| 2024-03-14 09:30 | War room call: Priya, Arjun, Kavitha, Vikram |
| 2024-03-14 10:45 | Root cause identified |
| 2024-03-14 11:00 | Sneha notifies stakeholders: *"Dashboard under investigation — data unreliable until 18:00 today"* |
| 2024-03-14 14:00 | Fix implemented and tested in dev environment |
| 2024-03-15 01:00 | Full re-run from Bronze (SCD-2 table rebuilt) |
| 2024-03-16 07:00 | Dashboard showing correct count (18,453) — verified by Rahul |
| 2024-03-16 09:00 | Incident closed, RCA shared with CIO |

---

## What Happened

The `02b_Silver_SCD2_NB.py` notebook was using the Silver dimension table's `updated_at` column as the watermark boundary — to identify which records to process incrementally.

**The problem**: SCD-2 inserts a **brand new row** whenever a patient attribute changes. This new row has `updated_at = today`. So the next day's incremental run would:
1. Read watermark: *"last run was yesterday at 01:15 AM"*
2. Query Silver: *"give me all patients with updated_at > yesterday"*
3. Find: all the SCD-2 new version rows inserted yesterday (which have updated_at = yesterday!)
4. Treat them as "incoming changes" and run SCD-2 AGAIN
5. Create yet more new version rows → repeat infinitely

The pipeline was essentially **self-feeding** — each run's output became the next run's input.

**Why didn't anyone catch it earlier?**
The patient count grew gradually at first (1.2× per day). Only on Day 3 did it become so obvious that the dashboard alarmed Rahul. The audit log showed correct row counts for Bronze but we weren't auditing Silver row counts independently.

---

## Root Cause

**Primary**: Watermark was incorrectly tracked on the **Silver SCD-2 table's** `updated_at` column instead of the **Bronze landing table's** `_load_timestamp`.

**Contributing factors**:
1. No Silver-layer row count monitoring alert (gap in ALT-007 scope)
2. Kavitha implemented SCD-2 based on a reference pattern that assumed a non-SCD source table
3. Code review by DE-002 (Arjun) missed this subtle distinction — SCD tables behave differently from standard tables

---

## Impact

- Gold layer patient KPIs inflated by 3× for 2 days
- Executive dashboard showed wrong patient counts on March 14–15
- CMO's clinical quality metrics (per-patient) were divided by wrong denominator
- Team spent 2 full days on investigation and fix
- Stakeholder trust impact (CMO's team questioned data reliability)

---

## Resolution

### Code Fix (02b_Silver_SCD2_NB.py — v1.4)
```python
# BEFORE (WRONG — v1.3):
# Watermark was read from silver.dim_patient.updated_at
incoming = spark.read.table("silver.dim_patient").filter(col("updated_at") > lit(watermark_val))

# AFTER (CORRECT — v1.4, INC-005 fix):
# Watermark is read from Bronze _load_timestamp — NOT Silver
incoming = spark.read.parquet(f"{MOUNT_POINT}/bronze/s1_patients/") \
    .filter(col("_load_date") == current_date())  # Only today's Bronze delta
```

### Architecture Rule Added
> **Rule DE-ARCH-007** (added to Architecture_Decisions.md):
> "Watermark tracking shall always reference the Bronze layer `_load_timestamp`. Silver SCD tables are never used as watermark sources."

### Monitoring Gap Fixed
- Added ALT-007b: Silver row count vs Bronze row count ratio alert (> 1.5× triggers WARNING)
- Added daily Silver dim_patient record count check in `05_Data_Quality_NB.py`

### SCD-2 Table Rebuild
1. Truncated `silver.dim_patient` (Silver only — Bronze was intact)
2. Re-ran full SCD-2 notebook from Day 1 Bronze data to rebuild correct history

---

## Lessons Learned

1. **Watermark should ALWAYS be on source/Bronze, never on a derived/transformed table**
2. **SCD-2 tables are not suitable as watermark sources** — their `updated_at` reflects the SCD insert time, not the source change time
3. **Add row count alerts at every layer** — not just Bronze
4. **Code review checklists need a specific SCD item**: "What is the watermark source? Is it Bronze or Silver?"

---

## Teams Chat (Reconstructed)

> **Rahul Nair** [08:17]: *"Hey team, something is seriously off with the patient count. 54k patients?? We had 18k yesterday"*

> **Arjun Patel** [08:19]: *"guys the patient count just tripled 💀 something is very wrong"*

> **Priya Sharma** [08:22]: *"@Kavitha drop everything. @Farhan pull the audit logs NOW. @Arjun check if any pipeline ran manually"*

> **Mohammed Farhan** [08:45]: *"Audit log shows Bronze_NB ran normally at 1:15 AM — 423 records. Nothing unusual"*

> **Kavitha Rajan** [09:08]: *"wait... I think I see it. The SCD2 notebook ran on Saturday AND Sunday AND today... and I think it's picking up its own output as new records"*

> **Priya Sharma** [09:10]: *"oh no. war room in 20 minutes. @Vikram please join"*

> **Vikram Krishnan** [09:30]: *"Kavitha's right. Classic self-feeding SCD issue. Watermark should be on Bronze, not Silver. We fix the source of truth"*

> **Priya Sharma** [11:00 to Sneha]: *"Please tell stakeholders dashboard is under maintenance. Do NOT share patient numbers until we confirm fix."*

> **Sneha Iyer** [11:05 to CMO/CFO]: *"The dashboard is currently under investigation for a data quality issue. We expect resolution by 18:00 today. Thank you for your patience."*

---

## Post-Incident Actions

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Add `_load_date` filter to all SCD notebooks | DE-003 | 2024-03-16 | ✅ Done |
| Update Architecture_Decisions.md (Rule DE-ARCH-007) | SA-001 | 2024-03-18 | ✅ Done |
| Add Silver row count DQ check | DE-004 | 2024-03-20 | ✅ Done |
| SCD code review checklist update | DE-001 | 2024-03-22 | ✅ Done |
| Share RCA with CIO (Ms. Divya) | PM-001 | 2024-03-16 | ✅ Done |

---
*MRHS Confidential | INC-005 Incident Report | Closed 2024-03-16*
