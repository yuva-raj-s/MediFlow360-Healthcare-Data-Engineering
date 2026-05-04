# Business Requirements Document (BRD)
## MediFlow360 — Unified Patient Intelligence Platform
**Document ID**: MRHS-BRD-001 | **Version**: 2.0 | **Date**: February 26, 2024
**Prepared by**: Sneha Iyer (PM-001) + Priya Sharma (DE-001)
**Approved by**: CIO, CMO, CFO

> **v2.0 Note**: This replaces BRD v1.0 (Jan 8, 2024). Major changes: BR-006 (fraud detection) added by CFO mid-sprint; KPI thresholds for BR-003 revised by CMO; BR-009 & BR-010 added after architecture review. See `16_change_requests/CR-001_Add_Fraud_Detection.md` and `16_change_requests/CR-002_KPI_Redefinition.md`.

---

## 1. Executive Summary

MRHS generates approximately 6,000 patient interactions per day across 4 hospitals. Data remains locked in 7 disconnected systems. This BRD defines the requirements for MediFlow360 — an Azure-based data platform that will consolidate, transform, and serve this data for executive, clinical, and operational decision-making.

---

## 2. Business Requirements

### BR-001: Unified Patient Master Index (UPMI)
**Priority**: P1 — Critical
**Requestor**: CMO (Dr. Meena), CIO (Ms. Divya)
**Problem**: A single patient visiting multiple MRHS hospitals gets different Patient IDs in each HIS. As a result, readmission calculations, longitudinal care tracking, and insurance claims reconciliation are unreliable.

**Requirement**:
- Implement probabilistic matching to deduplicate patient records across all 4 hospital HIS systems
- Matching keys: First Name, Last Name, Date of Birth, Phone Number (last 6 digits), Aadhaar hash (last 4 digits)
- Assign a single `global_patient_id` (MRHS-UPMI-XXXXXXXX) to each unique patient
- Confidence score threshold: ≥ 0.85 = auto-merge; 0.70–0.84 = flag for manual review; < 0.70 = separate records
- **SCD-2 Required**: Any change to matching attributes must create a new version row

**Acceptance Criteria**:
- Duplicate patient rate in silver layer < 0.5%
- UPMI lookup available as a gold layer dimension table
- Manual review queue exposed in Power BI with < 24hr SLA for resolution

---

### BR-002: Real-Time Claims Processing Analytics
**Priority**: P1 — Critical
**Requestor**: CFO (Mr. Balaji), Head of Billing (Ms. Shobha)
**Problem**: MRHS has no visibility into claims aging. By the time billing staff realise a claim has been denied, 45+ days have passed and the appeal window is nearly closed.

**Requirement**:
- Track every insurance claim from submission → in-review → approved/denied → payment
- Status transitions must be stored with timestamps (SCD-2 on fact_claims)
- Flag claims pending > 30 days as "At-Risk" with daily alert to billing team
- Detect anomaly: same procedure code billed > 2× in 7 days for the same patient
- Compute claims TAT (turnaround time) in business days
- Segment denial analysis by: payer, procedure code, hospital, attending physician

**KPIs**:
- Claims denial rate < 8% (revised from 10% in v1.0 — see CR-002)
- Average claims TAT < 12 business days
- 100% of claims with status transitions tracked

---

### BR-003: Clinical Quality Metrics (NABH Compliance)
**Priority**: P1 — Critical
**Requestor**: CMO (Dr. Meena), Compliance Officer (Ms. Preethi)

**Requirement**:
- 30-day readmission rate by: department, attending physician, diagnosis (ICD-10 code), hospital
- Medication error rate: total errors / total medication administrations × 1000
- Adverse event pipeline: capture all events tagged in HIS, route to compliance dashboard
- Length of stay (LOS) vs. DRG (Diagnosis Related Group) benchmark
- Surgical site infection rate by surgeon and procedure type

**KPIs** (revised in v2.0):
- 30-day readmission rate < 5% (was 7% in v1.0)
- Medication error rate < 2 per 1,000 administrations
- Adverse event report latency < 4 hours from occurrence to dashboard

---

### BR-004: Pharmacy Inventory Intelligence
**Priority**: P2 — High
**Requestor**: Head of Pharmacy (Mr. Rajan)

**Requirement**:
- Real-time drug inventory levels per hospital per ward
- Stockout prediction: 7-day forward-looking ML model (rule-based threshold in Phase 1)
  - Alert when: current_stock < avg_daily_consumption × 7
- Near-expiry alert: drugs expiring within 30 days
- Cross-hospital transfer recommendation: if Hospital A has surplus and Hospital B has shortage of same drug
- Drug pricing history via SCD-3 (current_price + previous_price)

**KPIs**:
- Zero stockout events for Schedule H drugs (critical medications)
- Drug wastage (expiry) < 1% of inventory value per quarter

---

### BR-005: Lab Turnaround Time (TAT) Monitoring
**Priority**: P2 — High
**Requestor**: Head of Diagnostics (Ms. Kaveri)

**Requirement**:
- Capture timestamps: specimen_collection → specimen_received_at_lab → result_validated → result_released
- TAT = result_released − specimen_collection (in hours)
- STAT (urgent) vs. Routine classification per test order
- Critical value alert pipeline: specific lab result thresholds trigger immediate alert
  - K+ > 6.5 mEq/L, Troponin > 0.40 ng/mL, Hb < 6 g/dL, PT-INR > 5.0, Glucose < 40 mg/dL
- Lab SLA breach report: tests that exceeded TAT SLA, by department, by shift

**KPIs**:
- Routine TAT < 4 hours (95th percentile)
- STAT TAT < 1 hour (95th percentile)
- 100% critical values flagged within 15 minutes of result release

---

### BR-006: Revenue Cycle Fraud Detection *(Added via CR-001, Week 5)*
**Priority**: P1 — Critical
**Requestor**: CFO (Mr. Balaji) — *Mid-sprint addition, see CR-001*

**Requirement**:
- Rule-based fraud scoring on all claims (ML deferred to Phase 2)
- Flag rules:
  - Rule F1: Same procedure billed > 2× per patient in 7 days → score +3
  - Rule F2: Bill amount > ₹2,00,000 → score +2
  - Rule F3: Claim submitted < 1 hour after patient discharge → score +2
  - Rule F4: Physician billed > 30 procedures in a single day → score +2
  - Rule F5: Diagnosis code does not match procedure code (ICD-CPT mismatch) → score +3
- Total score ≥ 5 → flag as HIGH RISK → alert to CFO + Billing Head immediately
- All fraud flags stored in `gold.fraud_flags` table with audit trail

**KPIs**:
- 100% of claims scored
- < 2% false positive rate (validated quarterly by billing team)

---

### BR-007: Executive KPI Dashboard SLA
**Priority**: P1 — Critical
**Requestor**: CEO (Dr. Ramesh), CMO, CFO

**Requirement**:
- All Gold layer KPIs refreshed and available by **07:00 AM IST daily** (Monday–Saturday)
- Power BI dashboard refresh scheduled for 06:30 AM
- If refresh fails → automated alert to PM-001 + DA-001 + CIO within 15 minutes
- Dashboard must show 12-month rolling trend for all KPIs
- Mobile-responsive report layout (CEO reviews on iPad)

**KPIs**:
- Dashboard availability SLA: 99.5% (≤ 3.65 missed days/year)
- Stale data incident response < 30 minutes

---

### BR-008: Data Lineage & Audit Trail
**Priority**: P1 — Critical
**Requestor**: CIO (Ms. Divya), Compliance Officer (Ms. Preethi)

**Requirement**:
- Every record traceable from source system → Bronze → Silver → Gold with timestamps
- Audit table must capture: source_system, pipeline_name, notebook_name, run_id, records_read, records_written, records_rejected, start_time, end_time, status
- Audit table is **immutable** — no UPDATE or DELETE allowed (append-only)
- Data lineage report available for NABH audit within 2 hours of request

---

### BR-009: Incremental Data Loads
**Priority**: P1 — Critical
**Requestor**: CIO (cost efficiency), OPS-001 (performance)

**Requirement**:
- Full loads only on Day 1 (initial load) and disaster recovery scenarios
- All subsequent loads must be incremental using appropriate pattern per source:
  - MySQL/PostgreSQL/Appointments: Watermark-based on updated_at timestamp
  - Lab SFTP: File-based (event-triggered on new file arrival)
  - Pharmacy: CDC via PostgreSQL WAL logical replication
  - HR Excel: Weekly full reload (< 500 rows, acceptable)
  - IoT Hub: 5-minute tumbling window micro-batch
- Late-arriving records: lookback window of 3 days for watermark-based sources
- Watermark table in Azure SQL to persist last-processed mark per entity

---

### BR-010: Slowly Changing Dimensions (SCD)
**Priority**: P1 — Critical
**Requestor**: CFO (billing audit), CMO (longitudinal patient tracking), Compliance

**Requirement**:
- SCD Type 1 (Overwrite): patient phone/email, ICD code descriptions, hospital config
- SCD Type 2 (Full History): patient address, insurance plan, provider department, claims status transitions
- SCD Type 3 (Current + Previous): drug pricing in pharmacy
- All SCD-2 tables must include: eff_start_date, eff_end_date, is_current, record_hash
- Change detection via SHA-256 hash of tracked columns
- SCD-2 history queryable for any point-in-time snapshot (for audit purposes)

---

## 3. Non-Functional Requirements Summary

| Category | Requirement |
|----------|-------------|
| Performance | Gold layer refresh < 90 minutes end-to-end |
| Availability | Pipeline SLA 99.5%; dashboard SLA 99.5% |
| Security | PII masked at Bronze→Silver; RBAC on all Azure resources |
| Compliance | DPDP Act 2023, NABH accreditation data requirements |
| Cost | Total Azure spend < $200 (free tier management) |
| Scalability | Architecture must support adding new source within 1 sprint |
| Auditability | 7-year data retention per NABH; immutable audit logs |

---

## 4. Glossary

| Term | Definition |
|------|------------|
| HIS | Hospital Information System — primary EHR for inpatient/outpatient data |
| LIS | Laboratory Information System — manages specimen tracking and lab results |
| MMIS | Materials Management Information System — pharmacy inventory system |
| SCD | Slowly Changing Dimension — technique to track historical changes in dimension tables |
| SHIR | Self-Hosted Integration Runtime — ADF component installed on-premises for local DB connectivity |
| TAT | Turnaround Time — time between process start and completion |
| DRG | Diagnosis Related Group — hospital reimbursement classification |
| NABH | National Accreditation Board for Hospitals & Healthcare Providers |
| DPDP | Digital Personal Data Protection Act, India 2023 |
| WAL | Write-Ahead Log — PostgreSQL change log used for CDC |

---

*MRHS Confidential | BRD v2.0 | Supersedes v1.0 (2024-01-08)*
