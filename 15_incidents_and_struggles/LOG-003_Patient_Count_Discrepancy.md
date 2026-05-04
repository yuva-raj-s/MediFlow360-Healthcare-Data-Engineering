# LOG-003: Patient Count Discrepancy
**Severity**: NA | **Status**: Resolved
**Author**: Sneha Iyer (PM-001)

**What Happened**:
Billing team complained our Power BI dashboard showed 18,400 patients, but their Excel report showed 19,200. They questioned data integrity.

**Root Cause**:
The Billing Excel did not deduplicate patients who visited multiple hospitals. Our Mediflow360 platform uses UPMI (Unified Patient Master Index) in the Silver layer, properly merging 800 duplicate records into single identities.
*Result: Dashboard was correct. Billing team now uses our Gold tables as the source of truth.*