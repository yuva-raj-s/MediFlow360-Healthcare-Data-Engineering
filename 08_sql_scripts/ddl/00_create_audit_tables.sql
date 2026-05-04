-- SQL Script: 08_sql_scripts/ddl/00_create_audit_tables.sql
-- MediFlow360 — Operational Telemetry & Audit Schema
-- Target: Azure SQL Database (mrhs-sqldb-meta)

CREATE SCHEMA mrhs_audit;
GO

CREATE SCHEMA bronze_meta;
GO

-- 1. Pipeline Audit Log (Immutable)
CREATE TABLE mrhs_audit.pipeline_audit_log (
    audit_id            INT IDENTITY(1,1) PRIMARY KEY,
    pipeline_name       NVARCHAR(100),
    notebook_name       NVARCHAR(100),
    run_id              NVARCHAR(100),
    source_system       NVARCHAR(50),
    entity_name         NVARCHAR(100),
    records_read        INT,
    records_written     INT,
    records_rejected    INT,
    status              NVARCHAR(20), -- SUCCESS, FAILED, PARTIAL
    start_time          DATETIMEOFFSET,
    end_time            DATETIMEOFFSET,
    duration_seconds    INT,
    error_message       NVARCHAR(MAX),
    created_at          DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);
GO

-- 2. Watermark Control Table
CREATE TABLE bronze_meta.watermark_control (
    entity_name             NVARCHAR(100) PRIMARY KEY,
    last_watermark_value    NVARCHAR(100),
    updated_at              DATETIMEOFFSET,
    last_pipeline_run_id    NVARCHAR(100)
);
GO

-- Seed initial watermarks for 7 sources
INSERT INTO bronze_meta.watermark_control (entity_name, last_watermark_value, updated_at)
VALUES 
('s1_patients', '1900-01-01 00:00:00', SYSDATETIMEOFFSET()),
('s4_appointments', '1900-01-01 00:00:00', SYSDATETIMEOFFSET()),
('s5_pharmacy', '1900-01-01 00:00:00', SYSDATETIMEOFFSET());
GO
