-- ============================================================
-- MediFlow360 | DDL: 05_create_watermark_table.sql
-- Author: Mohammed Farhan (DE-004) | Reviewed: Arjun Patel (DE-002)
-- Version: 1.0 | Date: 2024-01-28
-- Purpose: Watermark control table for incremental load tracking
-- ============================================================

USE MediFlow360;
GO

-- ============================================================
-- SCHEMA: bronze_meta
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'bronze_meta')
BEGIN
    EXEC ('CREATE SCHEMA bronze_meta')
END
GO

-- ============================================================
-- TABLE: watermark_control
-- Tracks last successfully processed watermark per entity.
-- Updated by: 07_Watermark_Manager_NB.py after each successful run.
-- ============================================================
IF OBJECT_ID('bronze_meta.watermark_control', 'U') IS NULL
BEGIN
    CREATE TABLE bronze_meta.watermark_control (
        watermark_id          INT IDENTITY(1,1) PRIMARY KEY,
        entity_name           VARCHAR(100)    NOT NULL UNIQUE,   -- e.g., 's1_patients'
        source_system         VARCHAR(50)     NOT NULL,          -- e.g., 'HIS-CHN'
        load_pattern          VARCHAR(20)     NOT NULL,          -- WATERMARK | FILE | CDC | FULL
        last_watermark_value  VARCHAR(50)     NOT NULL           -- ISO datetime or file name
                              DEFAULT '1900-01-01 00:00:00',
        last_successful_run   DATETIME2       NULL,
        last_pipeline_run_id  VARCHAR(200)    NULL,
        records_processed     BIGINT          NOT NULL DEFAULT 0,
        consecutive_failures  INT             NOT NULL DEFAULT 0,
        created_at            DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        updated_at            DATETIME2       NOT NULL DEFAULT GETUTCDATE()
    );

    -- Seed watermark entries for all 7 sources
    INSERT INTO bronze_meta.watermark_control
        (entity_name, source_system, load_pattern, last_watermark_value)
    VALUES
        ('s1_patients',         'HIS-CHN',        'WATERMARK', '1900-01-01 00:00:00'),
        ('s1_admissions',       'HIS-CHN',        'WATERMARK', '1900-01-01 00:00:00'),
        ('s2_claims',           'CLAIMS-API',      'WATERMARK', '1900-01-01 00:00:00'),
        ('s2_approvals',        'CLAIMS-API',      'WATERMARK', '1900-01-01 00:00:00'),
        ('s3_lab_results',      'LIS-SFTP',        'FILE',      'INITIAL'),
        ('s4_appointments',     'COSMOSDB-APPT',   'WATERMARK', '1900-01-01 00:00:00'),
        ('s5_pharmacy',         'PG-PHARMACY',     'CDC',       '0'),
        ('s5_drug_inventory',   'PG-PHARMACY',     'CDC',       '0'),
        ('s6_staff_roster',     'SHAREPOINT-HR',   'FULL',      'INITIAL'),
        ('s7_icu_vitals',       'IOTHUB-ICU',      'MICRO_BATCH','1900-01-01 00:00:00');

    PRINT 'watermark_control table created and seeded.'
END
GO

-- ============================================================
-- TABLE: file_audit_log
-- Tracks every SFTP file processed — prevents double processing.
-- ============================================================
IF OBJECT_ID('bronze_meta.file_audit_log', 'U') IS NULL
BEGIN
    CREATE TABLE bronze_meta.file_audit_log (
        file_audit_id     INT IDENTITY(1,1) PRIMARY KEY,
        source_system     VARCHAR(50)     NOT NULL,
        filename          VARCHAR(500)    NOT NULL,
        file_size_bytes   BIGINT          NULL,
        rows_loaded       INT             NULL,
        rows_rejected     INT             NULL DEFAULT 0,
        load_status       VARCHAR(20)     NOT NULL,   -- SUCCESS | FAILED | DUPLICATE
        load_timestamp    DATETIME2       NOT NULL DEFAULT GETUTCDATE(),
        pipeline_run_id   VARCHAR(200)    NULL,
        error_message     VARCHAR(MAX)    NULL,
        CONSTRAINT uq_file_audit UNIQUE (source_system, filename)  -- Prevent re-processing
    );
    PRINT 'file_audit_log table created.'
END
GO

-- ============================================================
-- STORED PROCEDURE: sp_get_watermark
-- Called by ADF Lookup Activity at start of each pipeline run.
-- ============================================================
CREATE OR ALTER PROCEDURE bronze_meta.sp_get_watermark
    @entity_name VARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;

    -- If no watermark exists, return sentinel value
    IF NOT EXISTS (SELECT 1 FROM bronze_meta.watermark_control WHERE entity_name = @entity_name)
    BEGIN
        SELECT '1900-01-01 00:00:00' AS last_watermark_value,
               @entity_name          AS entity_name,
               0                     AS records_processed;
        RETURN;
    END

    SELECT last_watermark_value, entity_name, records_processed, consecutive_failures
    FROM bronze_meta.watermark_control
    WHERE entity_name = @entity_name;
END
GO

-- ============================================================
-- STORED PROCEDURE: sp_update_watermark
-- Called by ADF Stored Procedure Activity AFTER successful copy.
-- ============================================================
CREATE OR ALTER PROCEDURE bronze_meta.sp_update_watermark
    @entity_name          VARCHAR(100),
    @new_watermark        VARCHAR(50),
    @pipeline_run_id      VARCHAR(200),
    @records_processed    BIGINT,
    @load_status          VARCHAR(20)     -- SUCCESS | FAILED
AS
BEGIN
    SET NOCOUNT ON;

    IF @load_status = 'SUCCESS'
    BEGIN
        UPDATE bronze_meta.watermark_control
        SET
            last_watermark_value  = @new_watermark,
            last_successful_run   = GETUTCDATE(),
            last_pipeline_run_id  = @pipeline_run_id,
            records_processed     = records_processed + @records_processed,
            consecutive_failures  = 0,
            updated_at            = GETUTCDATE()
        WHERE entity_name = @entity_name;
    END
    ELSE
    BEGIN
        -- On failure: increment failure counter, DON'T update watermark
        UPDATE bronze_meta.watermark_control
        SET
            consecutive_failures = consecutive_failures + 1,
            last_pipeline_run_id = @pipeline_run_id,
            updated_at           = GETUTCDATE()
        WHERE entity_name = @entity_name;

        -- Alert if 3 consecutive failures
        IF (SELECT consecutive_failures FROM bronze_meta.watermark_control WHERE entity_name = @entity_name) >= 3
        BEGIN
            RAISERROR('WATERMARK_ALERT: Entity %s has 3 consecutive failures. Manual intervention needed.', 16, 1, @entity_name);
        END
    END
END
GO

PRINT 'Watermark DDL complete: watermark_control, file_audit_log, sp_get_watermark, sp_update_watermark';
GO
