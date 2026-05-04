# Silver Layer Transformation Rules
- Standardize all text to UPPERCASE.
- Convert all timestamps to UTC.
- Handle NULLs: Strings="UNKNOWN", Integers=-1.
- Apply UPMI (Unified Patient Master Index) probabilistic matching to assign `global_patient_id`.