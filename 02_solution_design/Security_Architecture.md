# Security Architecture & Data Governance Framework
## MediFlow360 — Unified Patient Intelligence Platform
**Document ID**: MRHS-SEC-001 | **Version**: 2.0
**Architect**: Vikram Krishnan (SA-001) | **Data Governance Officer**: Lakshmi Venkat (DG-001)

---

## 1. Executive Summary
Security in MediFlow360 is paramount due to the strict regulatory requirements of healthcare data (DPDP Act 2023, NABH accreditation). The architecture implements a **Zero Trust Model**, ensuring that authentication, authorization, data encryption, and network isolation are enforced at every layer of the Medallion architecture—from source extraction via ADF through to Power BI consumption via Azure Synapse Analytics.

---

## 2. Identity and Access Management (IAM)

### 2.1 Microsoft Entra ID (formerly Azure AD) Integration
All components within the Azure ecosystem are integrated with a centralized Entra ID tenant.
- **Service Principals**: Used for automated programmatic access (e.g., Databricks to ADLS).
- **Managed Identities (MSI)**: 
  - System-Assigned Managed Identities are utilized by Azure Data Factory and Azure Synapse Analytics to authenticate against Azure Key Vault and ADLS Gen2 without storing explicit credentials.
- **Role-Based Access Control (RBAC)**:
  - `Storage Blob Data Contributor`: Granted to ADF and Databricks service principals.
  - Data Analysts do NOT receive raw ADLS ACLs; instead, access is governed centrally via Databricks Unity Catalog.

### 2.3 Databricks Unity Catalog Data Governance
MediFlow360 uses Unity Catalog to centralize access control, auditing, and data lineage across Databricks workspaces.
- **Fine-Grained Access Control**: Replaces legacy DBFS mounts and ADLS ACLs. We grant specific privileges on securable objects (`GRANT SELECT ON SCHEMA mediflow_prod.silver TO data_analysts`).
- **Automated Data Lineage**: Unity Catalog automatically tracks column-level lineage from the Bronze ingestion tables through to Gold aggregates, essential for compliance auditing.
- **Dynamic Data Masking**: Any PII fields not pre-hashed are masked dynamically at query time using Unity Catalog row filters and column masks.

### 2.2 Secret Management
**Azure Key Vault** acts as the central repository for all secrets, certificates, and connection strings.
- **NO Hardcoded Credentials**: None of the JSON pipeline definitions or Python notebooks contain clear-text passwords.
- **Databricks Secret Scopes**: Databricks connects to Key Vault via Azure-backed secret scopes (`dbutils.secrets.get()`).
- **Secret Rotation**: Database passwords (MySQL, PostgreSQL) are rotated every 90 days; Key Vault handles the lifecycle dynamically.

---

## 3. Network Security & Isolation

### 3.1 Azure Virtual Network (VNet)
The MediFlow360 platform components do not expose public endpoints.
- **VNet Injection**: Databricks Workspaces are deployed into a customer-managed VNet. Worker nodes sit in a private subnet, communicating with ADLS Gen2 via Private Endpoints.
- **Private Link**: Azure SQL Database and Azure Synapse Analytics are accessed exclusively over Azure Private Link, ensuring data traffic never traverses the public internet.
- **Self-Hosted Integration Runtime (SHIR)**: The on-premises MySQL HIS database in Chennai is securely accessed via an ADF SHIR installed behind the corporate firewall, requiring no inbound firewall ports to be opened.

### 3.2 Firewall Rules
- Azure Synapse and Azure SQL firewalls are configured to `Deny All` by default, explicitly allowing only the VNet subnets containing the Databricks clusters and Power BI Gateway.

---

## 4. Data Encryption

### 4.1 Encryption In Transit
- All data moving between on-premises sources and Azure, or between Azure services, is encrypted via **TLS 1.2+**.
- Database connections enforce SSL mode (e.g., PostgreSQL `sslmode=require`).

### 4.2 Encryption At Rest
- **Storage**: ADLS Gen2 utilizes Azure Storage Service Encryption (SSE) with Customer-Managed Keys (CMK) stored in Azure Key Vault.
- **Database**: Azure Synapse Dedicated SQL Pools and Azure SQL DB utilize Transparent Data Encryption (TDE).

---

## 5. Data Privacy & PII Masking

Under the DPDP Act 2023, Personally Identifiable Information (PII) must be obfuscated before landing in analytical (Silver/Gold) layers.

### 5.1 Databricks Masking Pipeline (Bronze → Silver)
The `01_Bronze_Ingestion_NB.py` applies deterministic transformations to PII columns:
1. **Aadhaar Numbers**: Hashed using PySpark `sha2(col, 256)`. This allows deterministic entity resolution (for the UPMI) without exposing the raw identifier.
2. **Phone Numbers**: Regex masking to show only the last 4 digits (`XXX-XXX-1234`).
3. **Patient Names**: Full names are retained in a secure mapping table accessible only to authorized Clinical Admins; analytics dashboards receive an anonymized `global_patient_id`.

### 5.2 Row-Level Security (RLS) in Azure Synapse Analytics
Synapse implements RLS to ensure consumers only see data they are authorized to view.
- **Implementation**: Inline Table-Valued Functions (TVF) paired with a Security Policy.
- **Logic**: 
  ```sql
  CREATE FUNCTION sec.fn_hospital_predicate(@HospitalCode varchar(10))
  RETURNS TABLE
  WITH SCHEMABINDING
  AS
  RETURN SELECT 1 AS fn_secure_result 
  WHERE @HospitalCode = CAST(SESSION_CONTEXT(N'UserHospital') AS varchar(10))
     OR IS_ROLEMEMBER('db_owner') = 1;
  ```
- **Power BI Propagation**: Power BI passes the logged-in user context (via DirectQuery Single Sign-On) to Synapse, inherently filtering fact tables at the database level.

---

## 6. Audit Logging & Monitoring
- **Immutability**: The `mrhs_audit.pipeline_logs` table in Azure SQL is append-only.
- **Azure Monitor**: Diagnostic settings for ADLS, Synapse, and ADF are piped to a Log Analytics Workspace for security incident and event management (SIEM) integration via Azure Sentinel.
- **Alerting**: Unauthorized access attempts on Synapse firewalls trigger immediate high-priority Logic App notifications to the SecOps team.

---
*MRHS Confidential | Security Architecture | v2.0*