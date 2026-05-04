# ADR 001: Azure SQL vs Synapse Analytics
**Date**: Feb 26, 2024 | **Owner**: SA-001
**Status**: Revised (Phase 2 Enterprise Scale)

### Context
With the expansion to 4 hospitals and petabyte-scale historical data (100M+ claims, IoT vitals), we need a robust serving layer for Power BI. In Phase 1 (PoC), Azure SQL Database was used due to free-tier constraints. For Phase 2, we are evaluating the production serving layer.

### Options
1. **Azure Synapse Dedicated SQL Pool (DW500c)**
2. **Azure SQL Database (Business Critical Tier)**

### Decision
**Azure Synapse Dedicated SQL Pool**.

### Justification
1. **Massively Parallel Processing (MPP)**: Synapse uses a distributed architecture (Hash/Replicate) allowing it to aggregate millions of IoT vitals and claims across 60 compute nodes simultaneously. Azure SQL is an SMP (Symmetric Multiprocessing) architecture that chokes on billion-row analytical queries.
2. **Direct integration with Databricks**: Databricks can bulk-load into Synapse using PolyBase (`com.databricks.spark.sqldw` connector) at speeds 10x faster than JDBC writes to Azure SQL.
3. **Cost vs Performance**: While Synapse carries a minimum footprint cost (~$5,500/mo for DW500c), it can be paused during off-hours, and it guarantees the sub-second DirectQuery latency required by the hospital CIOs. Azure SQL Business Critical at a similar performance tier would be comparable in cost but lack the MPP scaling.

### Consequences
- Requires Data Engineers to understand Synapse Distribution Keys (Hash vs Round Robin vs Replicate).
- Databricks notebooks must be updated to use the Synapse PolyBase connector with ADLS Gen2 staging directories. Azure SQL will be retained strictly for operational metadata (`watermark_table`) and audit logging.