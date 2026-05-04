# DPDP Act 2023 Compliance Checklist
## MediFlow360
**Owner**: Ms. Preethi Nair (Compliance Officer)

The Digital Personal Data Protection (DPDP) Act 2023 mandates specific handling of personal data. This checklist ensures the architecture complies.

### ✅ Notice and Consent (Section 5)
- [x] **Source System Responsibility**: Notice is collected at the HIS reception desk (S1) and App (S4). MediFlow360 only ingests data where consent flag = true.
- [ ] **Pending Action**: S4 MongoDB needs a `consent_revoked` flag synchronized to Silver via CDC to trigger hard deletion.

### ✅ Data Minimization (Section 6)
- [x] We only ingest columns explicitly required for KPI and Fraud modeling.
- [x] Aadhaar is immediately hashed in `01_Bronze_Ingestion_NB`. Raw Aadhaar is never written to ADLS.

### ✅ Data Retention (Section 8)
- [x] **Policy**: 7 years per NABH medical records policy.
- [x] **Implementation**: ADLS Lifecycle Management policy automatically moves `/bronze/` and `/silver/` to Archive (Cold storage) after 3 years, and deletes after 7 years.

### ✅ Right to Erasure (Section 12)
- [x] **Mechanism**: If a patient revokes consent or requests erasure, an event is published to Service Bus. Databricks job `Utility_Erase_Patient_NB` runs weekly to perform GDPR/DPDP-compliant hard deletes across Bronze/Silver Delta tables (Vaccuum executed).

### ❌ Breach Notification (Section 8.6)
- [x] **Status**: Near miss logged as INC-003. No external notification required, but internal alert ALT-010 created.