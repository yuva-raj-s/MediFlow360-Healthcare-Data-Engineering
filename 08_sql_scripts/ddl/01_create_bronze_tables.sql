-- ============================================================
-- MediFlow360 | DDL: 01_create_bronze_tables.sql
-- Author: Mohammed Farhan (DE-004) | Reviewed: Arjun Patel (DE-002)
-- Version: 1.0 | Date: 2024-01-22
-- ============================================================
USE MediFlow360;
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'bronze_meta')
    EXEC ('CREATE SCHEMA bronze_meta')
GO

-- Pipeline audit log (append-only, no UPDATE/DELETE)
IF OBJECT_ID('mrhs_audit.pipeline_audit_log', 'U') IS NULL
BEGIN
    EXEC ('CREATE SCHEMA mrhs_audit')
END
GO

CREATE TABLE mrhs_audit.pipeline_audit_log (
    audit_id           BIGINT IDENTITY(1,1) PRIMARY KEY,
    pipeline_name      VARCHAR(200)  NOT NULL,
    notebook_name      VARCHAR(200)  NOT NULL,
    run_id             VARCHAR(200)  NOT NULL,
    source_system      VARCHAR(100)  NOT NULL,
    entity_name        VARCHAR(200)  NOT NULL,
    records_read       BIGINT        NOT NULL DEFAULT 0,
    records_written    BIGINT        NOT NULL DEFAULT 0,
    records_rejected   INT           NOT NULL DEFAULT 0,
    status             VARCHAR(20)   NOT NULL,  -- SUCCESS | FAILED | PARTIAL
    start_time         DATETIME2     NOT NULL,
    end_time           DATETIME2     NOT NULL,
    duration_seconds   INT           NOT NULL,
    error_message      VARCHAR(MAX)  NULL,
    logged_at          DATETIME2     NOT NULL DEFAULT GETUTCDATE()
);
GO

-- Deny UPDATE and DELETE on audit table (immutability enforcement)
DENY UPDATE ON mrhs_audit.pipeline_audit_log TO PUBLIC;
DENY DELETE ON mrhs_audit.pipeline_audit_log TO PUBLIC;
GO

PRINT 'Bronze meta and audit schemas/tables created.';
GO
