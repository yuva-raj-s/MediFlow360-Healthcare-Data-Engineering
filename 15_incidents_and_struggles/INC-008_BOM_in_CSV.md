# INC-008: BOM in CSV Header
**Severity**: P2 | **Status**: Closed
**Author**: Kavitha Rajan (DE-003)

**What Happened**:
The Lab LIS system was updated by the vendor. The new export module added a hidden UTF-8 Byte Order Mark (BOM) `\ufeff` to the start of the CSV.
PySpark read the first column name as `\ufeffOrderID` instead of `OrderID`. This broke schema validation.

**Resolution**:
Wrote a `strip_bom()` Python utility function in `01_Bronze_Ingestion_NB.py` to aggressively clean column names.