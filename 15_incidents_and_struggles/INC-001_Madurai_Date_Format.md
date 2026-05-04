# INC-001: Madurai Date Format Outage
**Severity**: P2 | **Status**: Closed
**Author**: Arjun Patel (DE-002)

**What Happened**:
The S1 pipeline failed in Bronze validation. Madurai HIS sends `date_of_birth` as `MM-DD-YYYY`, while all other hospitals send `DD-MM-YYYY`. 
Databricks schema validation cast invalid dates to NULL. Null rate check in `01_Bronze_Ingestion_NB.py` fired ALT-006.

**Resolution**:
Added `normalize_date_column()` function in Bronze notebook that attempts `dd-MM-yyyy` parsing, and falls back to `MM-dd-yyyy`.