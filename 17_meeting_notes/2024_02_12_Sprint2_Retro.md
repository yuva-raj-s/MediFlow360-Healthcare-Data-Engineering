# Sprint 2 Retro
**What went well**:
- S3 (SFTP) and S4 (CosmosDB) ingestion completed ahead of schedule.

**What went wrong**:
- We hit INC-001 (Madurai Date Format). Our Bronze schema validation was too rigid.
- *Priya*: "We need to handle data quality defensively. Hospitals don't coordinate schema changes."

**Action Items**:
- Implement `normalize_date_column` in Bronze helper.