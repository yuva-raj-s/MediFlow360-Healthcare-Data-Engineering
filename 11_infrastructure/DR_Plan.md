# Disaster Recovery (DR) Plan

**RPO (Recovery Point Objective)**: 24 Hours
**RTO (Recovery Time Objective)**: 4 Hours

### Scenario: ADLS Gen2 Deletion
1. Pause ADF triggers.
2. Reset Azure SQL `watermark_control` to `1900-01-01`.
3. Trigger `PL_Master_Orchestrator`. This will pull all historical data from Source S1-S7.
4. Wait for Databricks notebooks to rebuild Silver and Gold layers.