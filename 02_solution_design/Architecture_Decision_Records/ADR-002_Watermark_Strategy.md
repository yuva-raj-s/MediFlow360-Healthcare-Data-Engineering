# ADR 002: Watermark Strategy
**Date**: Jan 12, 2024 | **Owner**: DE-002

### Context
We must prevent full reloads. Sources include MySQL, REST APIs, and CosmosDB.
### Decision
Centralized High-Watermark table in Azure SQL (`bronze_meta.watermark_control`).
### Justification
Standardizes ADF Lookup patterns. 
*Note: Post INC-005, we added Rule DE-ARCH-007 enforcing watermarks must read Bronze load timestamps, never Silver SCD timestamps.*