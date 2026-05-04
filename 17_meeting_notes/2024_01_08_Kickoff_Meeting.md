# Meeting Notes — Kickoff Meeting
## MediFlow360 | Date: January 8, 2024 | Time: 10:00 AM – 12:00 PM
**Location**: MRHS Chennai HQ, Conference Room 3B + Teams (remote)
**Facilitator**: Sneha Iyer (PM-001)
**Note-taker**: Mohammed Farhan (DE-004)

**Attendees**:
- In person: Sneha Iyer, Arjun Patel, Mohammed Farhan, Lakshmi Venkat, Suresh Kumar
- Remote: Priya Sharma (Chennai WFH), Kavitha Rajan (Coimbatore), Rahul Nair (Madurai), Vikram Krishnan (Bangalore)
- Stakeholders (first 30 min): Ms. Divya Anand (CIO), Mr. Balaji Venkatesh (CFO), Dr. Meena Krishnaswamy (CMO)

---

## Agenda

1. Project overview and objectives (10 min) — CIO
2. Business requirements walkthrough (20 min) — PM
3. Technical architecture overview (20 min) — SA-001
4. Team introductions and roles (10 min) — PM
5. Q&A with stakeholders (15 min)
6. Sprint 1 planning preview (20 min) — Lead DE
7. Action items and next steps (5 min)

---

## Notes

### 1. CIO Opening Remarks (Ms. Divya Anand)

> *"MRHS has been operating in data silos for too long. We have 4 hospitals, 7 source systems, and no single view of our patient population. The board has asked for a quarterly KPI dashboard by Q2 — that's our hard deadline. I'm counting on this team to deliver."*

- CIO emphasized the **July 31 go-live** is non-negotiable (tied to NABH re-accreditation audit)
- Azure free trial is in use — strong emphasis on cost discipline
- CIO mentioned that the CFO will scrutinise claims analytics closely — "if we can reduce denial rate by 2%, it's ₹3 crore annually for MRHS"

### 2. Business Requirements

Sneha walked through the BRD v1.0. Key discussion points:

- **CMO (Dr. Meena)** asked why readmission rate threshold is 7% — "Our NABH target is 5%. Please set the KPI to 5% and alert me when it's above that."
  - **Action**: Sneha to update BRD v1.0 KPI for BR-003 to 5% threshold
  - *[Note: This was later formalised as CR-002]*

- **CFO (Balaji)** asked if fraud detection was in scope
  - Priya (remote): *"We have anomaly detection in BR-006 but it's rule-based for Phase 1"*
  - CFO: *"I want email alerts when a claim is flagged. Not weekly reports — immediate alerts."*
  - **Action**: Priya to assess alert implementation for fraud flags
  - *[Note: CFO returned in Week 5 to formally add fraud detection — CR-001]*

### 3. Architecture Walkthrough (Vikram Krishnan)

Vikram presented the medallion architecture diagram. Questions from the team:

- Arjun: *"What's our strategy for the MySQL HIS — it's on-prem at Chennai. Can ADF connect directly?"*
  - Vikram: *"We need a Self-Hosted Integration Runtime. Suresh, can you get one set up on the hospital server?"*
  - Suresh: *"I'll need IT Infra's approval for opening the firewall. Let me talk to Anand (STK-009)."*
  - **Action**: Suresh to coordinate SHIR installation with IT Infra team by Jan 12

- Kavitha: *"Are we using Delta Lake or standard Parquet for Bronze?"*
  - Vikram: *"Community Edition doesn't support Delta natively. We'll use Parquet + MERGE via pandas/PySpark. Delta upgrade possible in Phase 2."*

- Farhan: *"What about the Excel roster from HR? I've seen HR's Excel before — it has merged cells. ADF won't handle that."*
  - Arjun: *"Good catch. We'll need to normalise it in the Bronze notebook. Let's flag this as a risk."*
  - *[Note: This became LOG-004 — 3 weeks of pain]*

### 4. Team Introductions

Priya gave a quick team overview. Kavitha and Rahul introduced themselves (first project meeting). Farhan joined 2 weeks ago and this is his first enterprise data project.

### 5. Q&A with Stakeholders

Q: *How long will it take before the CMO can see the dashboard?* (Dr. Meena)
A: *"Our target is a working dashboard prototype by Sprint 3 (mid-March) and production-quality by May. Full go-live July 31."* (Sneha)

Q: *Can we trust the patient counts? Our billing team's Excel says 18,000 unique patients — will your platform match that?* (Ms. Shobha Pillai, Head of Billing — joined briefly)
A: *"During UAT, we'll reconcile our patient count against your master list. If there's a discrepancy, we'll do a root cause analysis."* (Priya)
*[Note: This exact question resurfaced during INC-001 and LOG-003]*

### 6. Sprint 1 Preview

Priya walked through Sprint 1 scope:
- Azure infrastructure provisioning (ADLS, ADF, Key Vault, SQL DB)
- SHIR installation for MySQL
- ADF linked service for MySQL and REST API claims
- Hello World ingestion pipeline (full load of patients)
- Onboarding documentation

---

## Action Items

| # | Action | Owner | Due |
|---|--------|-------|-----|
| A1 | Update BRD BR-003 KPI to 5% readmission threshold | PM-001 | Jan 10 |
| A2 | Coordinate SHIR installation with IT Infra (Anand) | OPS-001 | Jan 12 |
| A3 | Set up Databricks Community Edition accounts for all team | DE-003 | Jan 10 |
| A4 | Create Azure resource group and ADLS account | OPS-001 | Jan 12 |
| A5 | Distribute BRD v1.0 to all stakeholders for sign-off | PM-001 | Jan 10 |
| A6 | Write Project Charter and get CIO signature | PM-001 | Jan 10 |
| A7 | Create onboarding document for Farhan (1 week into project) | DE-001 | Jan 12 |
| A8 | Research HR Excel format — assess merged cell problem | DE-002 | Jan 15 |

---

## Next Meeting

**Sprint 1 Planning**: January 22, 2024 at 09:00 AM — same format (hybrid)

---
*MediFlow360 | Kickoff Meeting Notes | 2024-01-08 | Note-taker: DE-004*
