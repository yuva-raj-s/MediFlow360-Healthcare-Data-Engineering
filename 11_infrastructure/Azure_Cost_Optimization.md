# Azure Cost Optimization Strategies
**Goal**: Run entire enterprise pipeline on $0/month (Free Tier).

1. **Databricks**: Use Community Edition. Implemented 30-minute auto-terminate. (Saved $500/mo).
2. **Azure SQL**: Use Basic DTU tier (max 2GB). It is free for 12 months.
3. **Storage**: ADLS Gen2 LRS free tier gives 5GB. We run vacuum aggressively.
4. **ADF**: Stay under 5 DIUs and 50,000 activities per month. We use Watermarks instead of full reloads to minimize activity runs.