# Functional Requirements Document (FRD)
## MediFlow360 Data Platform
**Version:** 2.0 | **Author:** Sneha Iyer (PM-001)

This document translates the business needs from the BRD into specific functional system behaviors required for the MediFlow360 architecture.

### FR-01: Heterogeneous Data Ingestion
* **Description:** The system MUST extract data from 7 disparate source systems (MySQL, REST API, MongoDB, PostgreSQL, SFTP, SharePoint, IoT Hub) on a daily schedule.
* **Mechanism:** Azure Data Factory (ADF) pipelines using Linked Services. On-premises sources MUST route through the Self-Hosted Integration Runtime (SHIR).
* **Constraints:** Ingestion MUST complete within a 60-minute batch window.

### FR-02: Incremental Loading & Watermarking
* **Description:** The system MUST NOT perform full table unloads (to comply with Free Tier egress constraints).
* **Mechanism:** 
  * ADF will maintain a `watermark_control` table in Azure SQL.
  * ADF will query `MAX(updated_at)` from source and update the watermark post-success.
  * For REST APIs, the watermark will be passed as a URL parameter `?last_modified=YYYY-MM-DD`.

### FR-03: PII Obfuscation & Security
* **Description:** No raw Personally Identifiable Information (Aadhaar) can land in the Data Lake.
* **Mechanism:** 
  * The Databricks Bronze notebook MUST compute a SHA-256 hash of the `aadhaar_number` in memory before writing to ADLS.
  * Phone numbers MUST be masked `XXXXXX1234` using regex substitution.

### FR-04: Automated Data Quality Gating
* **Description:** Bad data must not pollute the Gold layer.
* **Mechanism:** 
  * Databricks `05_Data_Quality_NB` MUST run validation checks (Null rates < 5%, referential integrity).
  * If the error threshold is breached, the notebook MUST throw an exception, failing the ADF pipeline and triggering ALT-006.

### FR-05: Incident & Anomaly Alerting
* **Description:** The system MUST proactively notify stakeholders of business anomalies.
* **Mechanism:** 
  * If Readmission Rate > 5% or Fraud Score >= 5, Databricks MUST issue an HTTP POST payload to the designated Microsoft Teams Webhook and Azure Logic App (for email routing).