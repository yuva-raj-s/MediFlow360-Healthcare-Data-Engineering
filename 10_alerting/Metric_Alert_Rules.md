# Azure Monitor Metric Alerts

1. **Storage Quota**:
   - Scope: `mrhsadlsprod`
   - Condition: `UsedCapacity` > 4 GB
   - Action: `mrhs-ag-primary`
2. **SQL DB DTU**:
   - Scope: `mrhs-sqldb-prod`
   - Condition: `DTU percentage` > 90% for 15 mins.
   - Action: `mrhs-ag-primary`