# ADR 003: Databricks Community Edition
**Date**: Jan 14, 2024 | **Owner**: SA-001

### Context
Azure Databricks Standard costs DBU + VM compute.
### Decision
Use Databricks Community Edition with simulated Key Vault scopes.
### Justification
Strict $0 budget.
### Trade-offs
No automated Jobs API integration with ADF. We simulate it via Web Activities in ADF triggering Community Edition endpoints (or manual triggering). Cluster auto-terminate must be strictly 30 mins (See LOG-002).