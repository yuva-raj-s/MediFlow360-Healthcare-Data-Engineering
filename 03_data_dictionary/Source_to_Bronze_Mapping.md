# Source-to-Bronze Mapping Document
## MediFlow360 | Document ID: MRHS-MAP-001 | Version: 1.3
**Author**: Arjun Patel (DE-002) | **Reviewed by**: Priya Sharma (DE-001), Lakshmi Venkat (DG-001)

---

## Source S1: MySQL HIS Chennai — Patients

**Connector**: ADF MySQL + Self-Hosted IR (mrhs-shir-chennai)
**Auth**: Username `adf_reader` / Password from Key Vault secret `mysql-his-chennai-pwd`
**Load Pattern**: Incremental Watermark on `updated_at`
**Bronze Path**: `/bronze/s1_patients/YYYY/MM/DD/patients_delta_YYYYMMDD_HHMMSS.parquet`

| Source Column | Source Type | Bronze Column | Bronze Type | Transformation | PII? | Notes |
|--------------|-------------|---------------|-------------|----------------|------|-------|
| patient_id | INT | patient_id_src | STRING | CAST to STRING, prefix "HIS-CHN-" | No | Source PK |
| first_name | VARCHAR(100) | first_name | STRING | TRIM, UPPER | **YES** | Mask in Silver |
| last_name | VARCHAR(100) | last_name | STRING | TRIM, UPPER | **YES** | Mask in Silver |
| date_of_birth | DATE | date_of_birth | DATE | Validate MM-DD-YYYY vs DD-MM-YYYY | **YES** | INC-001 root cause |
| gender | CHAR(1) | gender | STRING | Map M→Male, F→Female, O→Other | No | |
| phone_number | VARCHAR(15) | phone_number_raw | STRING | Land raw; mask in Silver | **YES** | |
| aadhaar_number | CHAR(12) | aadhaar_hash | STRING | SHA-256 in Bronze_NB; never store raw | **YES** | PII-CRITICAL |
| address_line1 | VARCHAR(255) | address_line1 | STRING | TRIM | **YES** | SCD-2 tracked |
| city | VARCHAR(100) | city | STRING | TRIM, UPPER | No | |
| pincode | CHAR(6) | pincode | STRING | Validate 6-digit numeric | No | |
| insurance_plan_id | INT | insurance_plan_id | STRING | CAST to STRING | No | FK to insurance dim |
| blood_group | VARCHAR(5) | blood_group | STRING | Validate against enum | No | |
| admission_count | INT | admission_count | INT | Direct copy | No | |
| created_at | DATETIME | created_at | TIMESTAMP | UTC conversion | No | |
| updated_at | DATETIME | updated_at | TIMESTAMP | UTC conversion; WATERMARK FIELD | No | |
| — | — | _src_system | STRING | Literal "HIS-CHN" | No | Added by pipeline |
| — | — | _load_timestamp | TIMESTAMP | current_timestamp() | No | Watermark base |
| — | — | _pipeline_run_id | STRING | ADF run ID parameter | No | |

---

## Source S2: REST API — Insurance Claims

**Connector**: ADF HTTP Connector
**Auth**: OAuth2 Client Credentials; token refreshed via Web Activity before Copy
**Token URL**: `https://claims-api.insurancepartner.in/oauth/token` (stored in KV: `claims-api-token-url`)
**Base URL**: `https://claims-api.insurancepartner.in/v2/claims`
**Pagination**: `?page={page_num}&size=500` (ADF pagination rule: nextPageUrl in response body)
**Load Pattern**: Incremental Watermark on `claim_date`
**Bronze Path**: `/bronze/s2_claims/YYYY/MM/DD/claims_delta_YYYYMMDD.json`

| Source JSON Field | Type | Bronze Column | Bronze Type | Transformation | Notes |
|------------------|------|---------------|-------------|----------------|-------|
| data[].claimId | string | claim_id | STRING | Direct | PK |
| data[].patientMRN | string | patient_mrn_src | STRING | Direct | Map to UPMI in Silver |
| data[].hospitalCode | string | hospital_code | STRING | Direct | |
| data[].procedureCode | string | procedure_code | STRING | TRIM | CPT code |
| data[].diagnosisCode | string | diagnosis_code | STRING | TRIM | ICD-10 |
| data[].claimDate | string | claim_date | DATE | Parse ISO 8601 | WATERMARK |
| data[].claimAmount | number | claim_amount_inr | DECIMAL(12,2) | Direct | |
| data[].status | string | status | STRING | Validate enum | SCD-2 |
| data[].payerCode | string | payer_code | STRING | Direct | |
| data[].attendingPhysicianId | string | physician_id | STRING | Direct | |
| data[].submissionTimestamp | string | submission_ts | TIMESTAMP | UTC parse | |
| data[].lastUpdated | string | last_updated_ts | TIMESTAMP | UTC parse | |
| meta.totalRecords | integer | — | — | Used for pagination | |
| meta.nextPageUrl | string | — | — | ADF pagination token | |
| — | — | _src_system | STRING | "CLAIMS-API" | |
| — | — | _load_timestamp | TIMESTAMP | current_timestamp() | |
| — | — | _pipeline_run_id | STRING | ADF run ID | |

---

## Source S3: SFTP — Lab Results (LIS)

**Connector**: ADF SFTP Connector
**Auth**: SSH Private Key from Key Vault secret `sftp-lis-private-key`
**SFTP Host**: `lis-sftp.mrhs-labs.in` Port: 22
**Remote Path**: `/outbound/lab_results/` (new files dropped by LIS at ~03:00 AM)
**Load Pattern**: File-based (ADF event trigger on new blob after SFTP copy to ADLS landing zone)
**File Format**: CSV, UTF-8 (except INC-008: BOM prefix — handled by BOM stripping in Bronze_NB)
**Bronze Path**: `/bronze/s3_lab_results/YYYY/MM/DD/<filename>.parquet`

| Source Column | Source Type | Bronze Column | Bronze Type | Transformation | Notes |
|--------------|-------------|---------------|-------------|----------------|-------|
| OrderID | VARCHAR | order_id | STRING | TRIM | PK |
| PatientMRN | VARCHAR | patient_mrn_src | STRING | TRIM | |
| TestCode | VARCHAR | test_code | STRING | TRIM, UPPER | LOINC code |
| TestName | VARCHAR | test_name | STRING | TRIM | |
| SpecimenCollected | DATETIME | specimen_collected_ts | TIMESTAMP | Handle both DD-MM-YYYY and MM-DD-YYYY | TAT calc start |
| SpecimenReceived | DATETIME | specimen_received_ts | TIMESTAMP | Parse | |
| ResultValidated | DATETIME | result_validated_ts | TIMESTAMP | Parse | |
| ResultReleased | DATETIME | result_released_ts | TIMESTAMP | Parse | TAT calc end |
| ResultValue | VARCHAR | result_value | STRING | Raw; typed in Silver | |
| ResultUnit | VARCHAR | result_unit | STRING | TRIM | |
| ReferenceRangeLow | DECIMAL | ref_range_low | DECIMAL | Parse | |
| ReferenceRangeHigh | DECIMAL | ref_range_high | DECIMAL | Parse | |
| IsCritical | BIT | is_critical_flag | INT | 0/1 | |
| OrderType | VARCHAR | order_type | STRING | STAT / ROUTINE | |
| OrderingDeptCode | VARCHAR | dept_code | STRING | TRIM | |
| \ufeffpatient_id (BOM) | VARCHAR | — | — | BOM stripped in Bronze_NB (INC-008) | Handle malformed header |
| — | — | _src_filename | STRING | Original SFTP filename | Audit trail |
| — | — | _src_system | STRING | "LIS-SFTP" | |
| — | — | _load_timestamp | TIMESTAMP | current_timestamp() | |

---

## Source S4: MongoDB / CosmosDB — Appointments

**Connector**: ADF CosmosDB SQL API Connector
**Auth**: Connection String from Key Vault secret `cosmosdb-appointments-connstr`
**Database**: `mrhs-appointments` | **Container**: `appointments`
**Load Pattern**: Incremental Watermark on `modifiedTimestamp`
**Bronze Path**: `/bronze/s4_appointments/YYYY/MM/DD/appointments_delta_YYYYMMDD.json`
**Note**: Documents have nested `patientSnapshot` object — flattened in Silver

| Source JSON Field | Type | Bronze Column | Bronze Type | Notes |
|------------------|------|---------------|-------------|-------|
| id | string | appointment_id | STRING | CosmosDB doc ID |
| patientSnapshot.mrn | string | patient_mrn_src | STRING | Embedded; map to UPMI in Silver |
| patientSnapshot.name | string | patient_name_raw | STRING | PII; mask in Silver |
| hospitalCode | string | hospital_code | STRING | |
| departmentCode | string | dept_code | STRING | |
| physicianId | string | physician_id | STRING | |
| appointmentDate | string | appointment_date | DATE | ISO 8601 |
| appointmentTime | string | appointment_time | STRING | HH:MM:SS |
| status | string | status | STRING | SCHEDULED/COMPLETED/CANCELLED/NO_SHOW |
| appointmentType | string | appointment_type | STRING | OP/IP/EMERGENCY/FOLLOWUP |
| chiefComplaint | string | chief_complaint | STRING | Free text; no PII expected |
| createdTimestamp | string | created_ts | TIMESTAMP | |
| modifiedTimestamp | string | modified_ts | TIMESTAMP | WATERMARK FIELD |
| _etag | string | — | — | CosmosDB internal; discard |
| — | — | _src_system | STRING | "COSMOSDB-APPT" |
| — | — | _load_timestamp | TIMESTAMP | current_timestamp() |

---

## Source S5: PostgreSQL — Pharmacy (CDC via WAL)

**Connector**: ADF PostgreSQL Connector (CDC mode)
**Auth**: SSL + Username `adf_pg_reader` / Password from KV secret `pg-pharmacy-pwd`
**Host**: `mrhs-pharmacy-pg.postgres.database.azure.com` Port: 5432
**WAL Config**: `wal_level=logical`, replication slot: `adf_pharmacy_slot`
**Load Pattern**: CDC — captures INSERT, UPDATE, DELETE with `op_type` column
**Bronze Path**: `/bronze/s5_pharmacy/YYYY/MM/DD/pharmacy_cdc_YYYYMMDD_HHMMSS.parquet`

| CDC Field | Bronze Column | Bronze Type | Notes |
|-----------|---------------|-------------|-------|
| __op | op_type | STRING | 'I'=Insert, 'U'=Update, 'D'=Delete |
| __commit_ts | commit_timestamp | TIMESTAMP | CDC event time; ordering key |
| __before | before_image | STRING | JSON of row before change (UPDATE/DELETE) |
| drug_id | drug_id | STRING | PK |
| drug_name | drug_name | STRING | |
| generic_name | generic_name | STRING | |
| drug_category | drug_category | STRING | Schedule H, OTC, etc. |
| current_stock_qty | current_stock_qty | INT | Per hospital per ward |
| unit_of_measure | unit_of_measure | STRING | tablets/ml/vials |
| current_price | current_price | DECIMAL(10,2) | SCD-3 in Silver |
| expiry_date | expiry_date | DATE | |
| hospital_code | hospital_code | STRING | |
| ward_code | ward_code | STRING | |
| reorder_level | reorder_level | INT | Stockout alert threshold |
| is_deleted | is_deleted | BOOLEAN | Soft delete for 'D' ops |
| updated_at | updated_at | TIMESTAMP | |
| — | _src_system | STRING | "PG-PHARMACY" |
| — | _load_timestamp | TIMESTAMP | current_timestamp() |

---

## Source S6: SharePoint Excel — HR Staff Roster

**Connector**: ADF HTTP Connector (SharePoint REST API)
**Auth**: Service Principal with SharePoint.ReadAll scope; client_id/secret in Key Vault
**URL Pattern**: `https://mrhs.sharepoint.com/sites/HR/Shared%20Documents/Rosters/staff_roster_weekNN_YYYY.xlsx`
**Load Pattern**: Full weekly reload every Monday 06:00 AM (< 500 rows)
**Known Issue**: File has merged header cells (LOG-004) — Bronze_NB applies header normalisation
**Bronze Path**: `/bronze/s6_hr_roster/YYYY/WW/staff_roster_week<NN>.parquet`

| Excel Column (raw) | Bronze Column | Bronze Type | Transformation | Notes |
|-------------------|---------------|-------------|----------------|-------|
| Employee ID | employee_id | STRING | TRIM | PK |
| Full Name | employee_name | STRING | TRIM | PII |
| Department | department | STRING | TRIM, UPPER | |
| Designation | designation | STRING | TRIM | |
| Hospital | hospital_code | STRING | Map to code | |
| Shift Type | shift_type | STRING | Morning/Evening/Night | |
| Week Start Date | week_start_date | DATE | Parse DD-MM-YYYY | |
| Week End Date | week_end_date | DATE | Parse | |
| Contact Number | contact_number | STRING | PII; mask in Silver | |
| — (merged header) | — | — | Skip merged rows | LOG-004 |
| — | _src_filename | STRING | Excel filename | |
| — | _src_system | STRING | "SHAREPOINT-HR" | |
| — | _load_timestamp | TIMESTAMP | current_timestamp() | |

---

## Source S7: Azure IoT Hub — ICU Vitals

**Connector**: ADF Event Hub Consumer (IoT Hub built-in endpoint)
**Auth**: SAS Token `mrhs-iothub-prod` / consumer group `adf-consumer`
**Trigger**: ADF Tumbling Window (5-minute batches)
**Bronze Path**: `/bronze/s7_icu_vitals/YYYY/MM/DD/HH/vitals_YYYYMMDD_HHMM.parquet`
**Payload Format**: JSON telemetry from each bedside device

| IoT Payload Field | Bronze Column | Bronze Type | Notes |
|------------------|---------------|-------------|-------|
| deviceId | device_id | STRING | IoT Hub device ID |
| body.bedId | bed_id | STRING | Unique bed identifier |
| body.hospitalCode | hospital_code | STRING | |
| body.wardCode | ward_code | STRING | ICU/CCU/NICU |
| body.patientMRN | patient_mrn_src | STRING | May be null if bed unoccupied |
| body.heartRate | heart_rate_bpm | INT | Beats per minute |
| body.spO2 | spo2_pct | DECIMAL(5,2) | Oxygen saturation % |
| body.systolicBP | systolic_bp_mmhg | INT | |
| body.diastolicBP | diastolic_bp_mmhg | INT | |
| body.temperature | temperature_celsius | DECIMAL(4,1) | |
| body.respiratoryRate | respiratory_rate_bpm | INT | |
| body.alertFlags | alert_flags | STRING | JSON array of active alerts |
| enqueuedTimeUtc | enqueued_ts | TIMESTAMP | IoT Hub ingestion time |
| — | _src_system | STRING | "IOTHUB-ICU" |
| — | _batch_window_start | TIMESTAMP | Tumbling window start |
| — | _load_timestamp | TIMESTAMP | current_timestamp() |

---

## General Bronze Layer Standards

All Bronze tables/files include the following audit columns regardless of source:

| Column | Type | Description |
|--------|------|-------------|
| _src_system | STRING | Source system identifier |
| _load_timestamp | TIMESTAMP | When the record was loaded |
| _pipeline_run_id | STRING | ADF pipeline run ID |
| _load_date | DATE | Partition date (derived from _load_timestamp) |

**Partitioning Strategy**: All Bronze data partitioned by `_load_date` (YYYY/MM/DD folder hierarchy).

---
*MRHS Confidential | Source-to-Bronze Mapping | v1.3*
