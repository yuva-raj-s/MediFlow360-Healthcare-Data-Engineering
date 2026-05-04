# New Team Member Onboarding Guide
## MediFlow360 — MediCare Regional Health System
**Document ID**: MRHS-ONB-001 | **Version**: 1.1 | **Date**: January 15, 2024
**Author**: Priya Sharma (DE-001) | **HR Contact**: sneha.iyer@mrhs-de.in

---

> Welcome to the MediFlow360 team! This guide will take you from zero to productive in 30 days.
> Before anything else, please read the **Welcome Letter** in this folder from Priya.
> If you get stuck at any point, ping **#mediflow360-dev** on Teams — someone will help within an hour.

---

## Week 1 — Orientation & Access Setup

### Day 1: Accounts & Access
- [ ] Receive Azure AD credentials from Suresh (OPS-001) — check your MRHS email
- [ ] Complete Azure AD MFA setup (Authenticator app required)
- [ ] Get added to Azure subscription `mrhs-azure-free-trial` by OPS-001
- [ ] Request access to Databricks Community Edition workspace (separate login — see `Databricks_Community_Setup.md`)
- [ ] Join Teams channels: `#mediflow360-dev`, `#mediflow360-alerts`, `#mediflow360-incidents`
- [ ] Get Azure DevOps access from OPS-001 — repo: `mrhs-org/mediflow360`
- [ ] Clone the repo: `git clone https://mrhs-org.visualstudio.com/mediflow360/_git/mediflow360`

### Day 1: Read These Documents (In Order)
1. `00_project_charter/Project_Charter.md` — 15 min read
2. `00_project_charter/Stakeholder_Register.md` — know the stakeholders
3. `01_business_requirements/BRD_MediFlow360_v2.0.md` — 30 min read
4. `02_solution_design/HLD_High_Level_Design.md` — understand the architecture
5. This document — you're here!

### Day 2: Environment Setup
- Follow `Dev_Environment_Setup.md` completely
- Install: Python 3.10+, VS Code, Azure CLI, Azure Storage Explorer, Git
- Verify you can log into Azure Portal: https://portal.azure.com
- Verify you can see resource group `mrhs-rg-mediflow360`

### Day 3–4: Data Understanding
- Read `03_data_dictionary/Source_to_Bronze_Mapping.md`
- Read `03_data_dictionary/Data_Dictionary_All_Layers.md`
- Read `03_data_dictionary/SCD_Design_Document.md`
- Ask Kavitha (DE-003) for a walkthrough of the Silver notebooks

### Day 5: Meet the Team
- 1:1 with Priya Sharma (Lead DE) — 30 min intro call
- 1:1 with Arjun Patel (Senior DE) — ADF pipeline walkthrough
- 1:1 with Rahul Nair (DA) — understand what dashboards need from Gold layer
- Attend your first daily standup (09:00 AM Teams)

---

## Week 2 — Technical Deep Dive

### Databricks Environment
- Log in to Databricks Community Edition: https://community.cloud.databricks.com
- The shared cluster is named `mrhs-shared-cluster-01` (Standard_DS3_v2, Spark 3.3)
- **IMPORTANT**: Always terminate the cluster when you're done. Forgetting costs credits (see `15_incidents_and_struggles/LOG-002_Azure_Cost_Overrun.md`)
- Import notebooks from `/07_notebooks/` into your Databricks workspace
- Run `00_Helper_NB.py` first to verify Key Vault connectivity

### Azure Data Factory
- ADF URL: `https://adf.azure.com` → Select `mrhs-adf-prod`
- Review each pipeline in `09_adf_pipelines/pipeline_configs/`
- **DO NOT trigger pipelines manually during business hours** — always use test environment
- Full pipeline: `PL_Master_Orchestrator` → triggers all 8 child pipelines in sequence

### Key Vault Access
- Key Vault: `mrhs-kv-prod`
- You have **Read** access to secrets (not write)
- To add/modify secrets, request via OPS-001 with justification
- Never print secret values in notebook output — use `dbutils.secrets.get()` only

### ADLS Gen2 Structure
```
mrhsadlsprod/
├── bronze/    (you have Write access)
├── silver/    (you have Write access — through notebooks only)
├── gold/      (you have Read access; writes only via Gold_NB)
├── archive/   (Read only)
└── configs/   (Read only — schema registry)
```

---

## Week 3 — First Contribution

### Your First Task
Your first task will be assigned by Priya after Week 2 review. Typical first tasks:
- Write a data quality check in `05_Data_Quality_NB.py` for a new entity
- Add a SQL monitoring query in `08_sql_scripts/monitoring/`
- Write test cases in `12_testing/Unit_Test_Cases.md`
- Help with a sprint backlog item in `18_sprint_artifacts/`

### Git Workflow (Read `04_onboarding/Git_Workflow_Guide.md`)
- **Never commit directly to `main`**
- Branch naming: `feature/DE-004-add-lab-dq-checks`
- PR requires 1 approval from senior (DE-001 or DE-002) before merge
- PR description template is in the repo's `.github/pull_request_template.md`

### Code Standards
- All PySpark notebooks must: import from Helper_NB, write to audit table, handle exceptions with alert dispatch
- All SQL scripts must: include header comment with purpose, author, date
- All changes must reference a Jira ticket or sprint backlog item in commit message

---

## Week 4 — Independence

By end of Week 4, you should be able to:
- [ ] Independently navigate all Azure resources
- [ ] Run a pipeline end-to-end in the test environment
- [ ] Interpret Azure Monitor alerts
- [ ] Write a Silver transformation for a new entity
- [ ] Raise and document a data quality issue properly

### Useful Contacts (Quick Reference)

| Who | When to contact | Teams handle |
|-----|----------------|--------------|
| Priya Sharma | Architecture questions, escalations | @priya.sharma |
| Arjun Patel | ADF pipeline issues, SHIR problems | @arjun.patel |
| Kavitha Rajan | Databricks notebook errors, PySpark | @kavitha.rajan |
| Mohammed Farhan | SQL script questions, test cases | @farhan.m |
| Suresh Kumar | Azure access, Key Vault, DevOps | @suresh.kumar |
| Sneha Iyer | Sprint planning, stakeholder queries | @sneha.iyer |

---

## Common Gotchas (Learn from Our Mistakes!)

| # | Gotcha | What happened | Lesson |
|---|--------|--------------|--------|
| 1 | **Date format mismatch** | Madurai HIS sends MM-DD-YYYY; rest use DD-MM-YYYY | Always validate date format at Bronze |
| 2 | **Cluster left running** | $47 credit burned in a weekend | Auto-terminate: 30 min idle timeout |
| 3 | **Watermark on wrong table** | SCD-2 inserts pushed watermark forward → duplicates | Watermark always on Bronze, never Silver |
| 4 | **BOM in CSV** | `\ufeffpatient_id` as column name | Always strip BOM before reading SFTP files |
| 5 | **OAuth2 token URL change** | Claims API silently returned 401 for 14 hrs | Add response code validation in pipeline |
| 6 | **Aadhaar in Gold layer** | Junior engineer cached PII accidentally | Never SELECT * in Gold notebooks |

---

## Resources

- Azure Portal: https://portal.azure.com
- Azure DevOps: https://mrhs-org.visualstudio.com/mediflow360
- Databricks Community: https://community.cloud.databricks.com
- Power BI Service: https://app.powerbi.com
- Teams Workspace: MRHS Data Platform
- Jira Board: https://mrhs.atlassian.net/jira/software/projects/MF360

---
*Welcome to the team! — Priya Sharma, Lead Data Engineer*
*MRHS Confidential | Onboarding Guide | v1.1*
