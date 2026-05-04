# Sprint 1 Retrospective
## MediFlow360 | Sprint: 1 (Jan 22 – Feb 2, 2024)
**Date**: February 5, 2024 | **Facilitator**: Sneha Iyer (PM-001)
**Format**: Start / Stop / Continue + Action Items

---

## Attendance

✅ Priya Sharma | ✅ Arjun Patel | ✅ Kavitha Rajan | ✅ Mohammed Farhan | ✅ Rahul Nair | ✅ Sneha Iyer | ✅ Suresh Kumar | ❌ Vikram Krishnan (conflict) | ❌ Lakshmi Venkat (on leave)

---

## Sprint 1 Goals Review

| Goal | Status | Comment |
|------|--------|---------|
| Azure infra provisioned (ADLS, ADF, SQL, KV) | ✅ Done | Suresh completed by Jan 16 |
| SHIR installed for MySQL HIS | ✅ Done | Jan 18 after firewall clearance |
| ADF linked services: MySQL + REST API | ✅ Done | Arjun finished Jan 20 |
| Full load: Patients from MySQL | ✅ Done | 18,421 records — validated Jan 26 |
| Full load: Claims from REST API | ⚠️ Partial | 23 of 30 pages loaded — pagination bug |
| Databricks environment for all team | ✅ Done | Kavitha completed Jan 15 |
| Onboarding doc for Farhan | ✅ Done | Priya wrote it in 2 hrs on Jan 12 |
| Hello World Silver notebook | ❌ Not started | Deprioritised — moved to Sprint 2 |

**Velocity**: 34 points planned → 28 points completed. (82%)

---

## What Went Well ✅ (Continue)

- **Suresh's infra speed**: Got ADLS, ADF, Key Vault, and SQL provisioned in 3 days. Nobody expected it to be that fast.
- **Kavitha's onboarding**: She got the Databricks environment set up for everyone including remote folks without a single support ticket.
- **Arjun's ADF expertise**: His SHIR setup was smooth. He found a clever retry logic for the MySQL connection that saved us from a potential INC-002 scenario early on.
- **Daily standup discipline**: Team is on time, focused, no fluff. 15 minutes max.

---

## What Didn't Go Well ❌ (Stop)

**Arjun**: *"The claims API pagination was completely undocumented. We assumed page=1 starts at 0 but it's 1-based indexing. Lost 3 hours debugging that."*
→ **Stop**: Assuming API documentation is correct without verification.

**Priya**: *"We merged Farhan's SQL script directly to main without a PR review. He had a missing semicolon that would have broken the audit table creation. We caught it in testing but we got lucky."*
→ **Stop**: Bypassing PR review process for 'small' changes.

**Kavitha**: *"I have no idea what the HR Excel looks like. Arjun said there are merged cells but nobody's actually looked at it yet. That's 3 weeks away and we're not prepared."*
→ **Stop**: Deferring known risks without investigation.

**Sneha**: *"Our sprint review with the CIO lasted 8 minutes. We had a lot to show and she had to leave early. I didn't prepare a crisp enough demo. Lesson learned."*
→ **Stop**: Showing raw notebooks to executives — they want dashboards.

---

## What Should We Start ➕ (Start)

**Priya**: *"We need a PR review checklist. Specifically for SCD notebooks — they have subtle bugs that aren't obvious."*
→ **Start**: PR checklist (added to Git_Workflow_Guide.md)

**Rahul**: *"Can we get a staging dashboard in Power BI now? Even if the data is fake. I need to start building layout so Gold layer design can be validated by analysts."*
→ **Start**: Rahul to build skeleton Power BI report in Sprint 2 using sample Gold data

**Suresh**: *"Let's set up Azure Budget alerts NOW before we forget. We're on free trial and one forgotten Databricks cluster can burn through credits."*
→ **Start**: Budget alert at $150 (before $200 limit). OPS-001 done by Feb 7.

**Farhan**: *"I want to actually read the Excel roster file before Sprint 3. Can someone send me a sample?"*
→ **Start**: Arjun to get sample Excel from HR by Feb 9 and brief Farhan.

---

## Team Morale Check (Anonymous Menti.com poll)

| Statement | Score (1–5 avg) |
|-----------|-----------------|
| I understand my role clearly | 4.3 |
| I feel the sprint was achievable | 3.8 |
| I feel supported by the team | 4.6 |
| I am worried about the July deadline | 3.2 |
| I would recommend this team to others | 4.7 |

*Note from Sneha: The "worried about July" score is 3.2 — lower than expected. I'll do 1:1s this week to understand concerns. The fact that we didn't complete the Silver hello-world is a signal we may be underestimating transformation complexity.*

---

## Action Items

| # | Action | Owner | Due |
|---|--------|-------|-----|
| A1 | Set Azure Budget alert at $150 | OPS-001 | Feb 7 |
| A2 | Get HR Excel sample, brief Farhan | DE-002 | Feb 9 |
| A3 | Fix claims pagination bug (1-based) | DE-002 | Feb 8 |
| A4 | Add PR checklist to Git_Workflow_Guide.md | DE-001 | Feb 9 |
| A5 | Build skeleton Power BI report with sample data | DA-001 | Sprint 2 |
| A6 | Raise the HR Excel merged-cell issue as Risk R-007 | PM-001 | Feb 7 |
| A7 | 1:1s with all team members re: July deadline anxiety | PM-001 | Feb 9 |

---

*MediFlow360 | Sprint 1 Retrospective | 2024-02-05 | Sneha Iyer (PM-001)*
