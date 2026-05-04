-- ============================================================
-- MediFlow360 | DDL: 02_create_silver_tables.sql
-- Author: Mohammed Farhan (DE-004) | Reviewed: Kavitha Rajan (DE-003)
-- Version: 1.2 | Date: 2024-02-10
-- Includes SCD-2 extra columns on all dimension tables
-- ============================================================
USE MediFlow360;
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'silver')
    EXEC ('CREATE SCHEMA silver')
GO

-- ============================================================
-- dim_patient: SCD-2 on address + insurance_plan
-- SCD-1 on phone_number, email (see separate MERGE proc)
-- ============================================================
CREATE TABLE silver.dim_patient (
    patient_sk           BIGINT IDENTITY(1,1) PRIMARY KEY,  -- Surrogate key
    global_patient_id    VARCHAR(50)     NOT NULL,           -- UPMI natural key
    patient_id_src       VARCHAR(50)     NOT NULL,           -- Source system PK
    src_system           VARCHAR(20)     NOT NULL,
    first_name           VARCHAR(100)    NOT NULL,
    last_name            VARCHAR(100)    NOT NULL,
    date_of_birth        DATE            NULL,
    gender               VARCHAR(10)     NULL,
    phone_number         VARCHAR(20)     NULL,               -- SCD-1 (last 4 visible, first 6 masked)
    email                VARCHAR(200)    NULL,               -- SCD-1
    address_line1        VARCHAR(255)    NULL,               -- SCD-2 tracked
    city                 VARCHAR(100)    NULL,               -- SCD-2 tracked
    pincode              CHAR(6)         NULL,               -- SCD-2 tracked
    insurance_plan_id    VARCHAR(50)     NULL,               -- SCD-2 tracked
    blood_group          VARCHAR(5)      NULL,
    aadhaar_hash         VARCHAR(64)     NULL,               -- SHA-256; NEVER store raw
    -- SCD-2 columns
    eff_start_date       DATE            NOT NULL,
    eff_end_date         DATE            NULL,               -- NULL = current record
    is_current           BIT             NOT NULL DEFAULT 1,
    record_hash          VARCHAR(64)     NOT NULL,           -- SHA-256 of SCD-2 tracked cols
    -- Audit
    created_by_run_id    VARCHAR(200)    NULL,
    updated_at           DATETIME2       NOT NULL DEFAULT GETUTCDATE()
);
GO

CREATE INDEX ix_dim_patient_upmi     ON silver.dim_patient (global_patient_id, is_current);
CREATE INDEX ix_dim_patient_eff_date ON silver.dim_patient (eff_start_date, eff_end_date);
GO

-- ============================================================
-- dim_provider: SCD-2 on department assignment
-- ============================================================
CREATE TABLE silver.dim_provider (
    provider_sk          BIGINT IDENTITY(1,1) PRIMARY KEY,
    physician_id         VARCHAR(50)     NOT NULL,
    first_name           VARCHAR(100)    NOT NULL,
    last_name            VARCHAR(100)    NOT NULL,
    designation          VARCHAR(100)    NULL,
    department_code      VARCHAR(50)     NULL,               -- SCD-2 tracked
    hospital_code        VARCHAR(20)     NULL,               -- SCD-2 tracked
    phone_number         VARCHAR(20)     NULL,               -- SCD-1
    email                VARCHAR(200)    NULL,               -- SCD-1
    -- SCD-2 columns
    eff_start_date       DATE            NOT NULL,
    eff_end_date         DATE            NULL,
    is_current           BIT             NOT NULL DEFAULT 1,
    record_hash          VARCHAR(64)     NOT NULL,
    created_by_run_id    VARCHAR(200)    NULL
);
GO

-- ============================================================
-- dim_drug: SCD-3 on price (current + previous only)
-- ============================================================
CREATE TABLE silver.dim_drug (
    drug_sk              BIGINT IDENTITY(1,1) PRIMARY KEY,
    drug_id              VARCHAR(50)     NOT NULL UNIQUE,
    drug_name            VARCHAR(200)    NOT NULL,
    generic_name         VARCHAR(200)    NULL,
    drug_category        VARCHAR(50)     NULL,               -- Schedule H, OTC, etc.
    unit_of_measure      VARCHAR(20)     NULL,
    current_price        DECIMAL(10,2)   NULL,               -- SCD-3
    previous_price       DECIMAL(10,2)   NULL,               -- SCD-3 (previous value only)
    price_changed_at     DATETIME2       NULL,               -- When price last changed
    reorder_level        INT             NULL,
    is_schedule_h        BIT             NOT NULL DEFAULT 0,
    updated_at           DATETIME2       NOT NULL DEFAULT GETUTCDATE()
);
GO

-- ============================================================
-- fact_claims: SCD-2 on status progression
-- ============================================================
CREATE TABLE silver.fact_claims (
    claim_sk             BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_id             VARCHAR(100)    NOT NULL,
    patient_sk           BIGINT          NULL,               -- FK to dim_patient (current)
    physician_id         VARCHAR(50)     NULL,
    hospital_code        VARCHAR(20)     NULL,
    procedure_code       VARCHAR(20)     NULL,
    diagnosis_code       VARCHAR(20)     NULL,
    claim_date           DATE            NULL,
    claim_amount_inr     DECIMAL(12,2)   NULL,
    status               VARCHAR(30)     NOT NULL,           -- SUBMITTED|IN_REVIEW|APPROVED|DENIED|PAID
    payer_code           VARCHAR(50)     NULL,
    submission_ts        DATETIME2       NULL,
    -- SCD-2 status history columns
    eff_start_date       DATE            NOT NULL,
    eff_end_date         DATE            NULL,
    is_current           BIT             NOT NULL DEFAULT 1,
    -- Audit
    created_by_run_id    VARCHAR(200)    NULL,
    fraud_score          INT             NOT NULL DEFAULT 0,
    fraud_flags          VARCHAR(MAX)    NULL
);
GO

CREATE INDEX ix_fact_claims_id      ON silver.fact_claims (claim_id, is_current);
CREATE INDEX ix_fact_claims_status  ON silver.fact_claims (status, claim_date);
GO

PRINT 'Silver schema tables created (dim_patient SCD-2, dim_drug SCD-3, fact_claims SCD-2).';
GO
