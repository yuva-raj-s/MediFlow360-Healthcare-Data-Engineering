# PII Classification Matrix
## MediFlow360 — Data Governance
**Document ID**: MRHS-DG-001 | **Version**: 1.2
**Owner**: Lakshmi Venkat (DG-001)

This document defines how Personally Identifiable Information (PII) is handled across the MediFlow360 architecture, ensuring compliance with the DPDP Act 2023.

### 1. Classification Levels

| Level | Definition | Handling Rule |
|-------|------------|---------------|
| **CRITICAL** | Direct identifiers (Aadhaar, PAN). High risk of identity theft. | Hash with SHA-256 before landing in Bronze. Raw data NEVER stored. |
| **HIGH** | Contact info (Phone, Email, Address). High risk of targeted contact. | Land in Bronze encrypted. Mask in Silver (e.g., `XXXXXX1234`). |
| **MEDIUM** | Demographic (DOB, Gender, Name). Risk when combined with other data. | Retain in Bronze/Silver. Restrict access in Gold using Row-Level Security. |
| **LOW** | System IDs (Patient_ID, Claim_ID). No external meaning. | No masking required. |

### 2. Attribute Matrix

| Source Entity | Attribute | DPDP Category | Classification | Transformation (Bronze -> Silver) | Notebook Reference |
|--------------|-----------|---------------|----------------|----------------------------------|--------------------|
| Patient (S1) | aadhaar_number | Critical Personal Data | CRITICAL | SHA-256 Hash -> `aadhaar_hash` | `01_Bronze_Ingestion_NB` |
| Patient (S1) | phone_number | Personal Data | HIGH | Mask first 6 digits -> `phone_masked` | `00_Helper_NB` (mask_phone) |
| Patient (S1) | address_line1 | Personal Data | HIGH | Encrypt at rest; strict RBAC | N/A |
| Staff (S6) | contact_number | Personal Data | HIGH | Mask first 6 digits | `01_Bronze_Ingestion_NB` |
| Claims (S2) | patientMRN | System ID | LOW | None | N/A |

### 3. Incident History
- **INC-003**: Junior DE inadvertently wrote partial Aadhaar (last 4 digits) to Gold layer `/debug/` folder. This violated the CRITICAL rule. As a result, automated PII scanning was implemented in `05_Data_Quality_NB` before any Gold write.

*MRHS Confidential | Data Governance*