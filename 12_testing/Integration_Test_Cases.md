# Integration Tests
- **ITC-01**: Trigger `PL_Ingest_Patients`. Verify Parquet file lands in `/bronze/s1_patients/YYYY/MM/DD/`.
- **ITC-02**: Trigger `02b_Silver_SCD2_NB.py`. Verify existing row `is_current` flips to 0, and new row is 1.
- **ITC-03**: Alter OAuth token in Key Vault. Verify pipeline fails and Teams alert is sent.