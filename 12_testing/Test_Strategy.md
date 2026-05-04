# Test Strategy

1. **Unit Testing (Local)**:
   - Framework: `pytest`
   - Coverage: Custom Python transformations (e.g., `strip_bom`, `mask_aadhaar`).
2. **Data Quality Testing (Pipeline)**:
   - Executed by `05_Data_Quality_NB.py`.
   - Checks: Null rates, Primary Key uniqueness, Referential integrity (FK to PK).
3. **UAT (Stakeholder)**:
   - End users validate Power BI dashboard numbers against their manual Excel reports.