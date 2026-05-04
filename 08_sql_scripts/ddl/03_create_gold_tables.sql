-- MediFlow360 | DDL: 03_create_gold_tables.sql
USE MediFlow360;
GO
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold') EXEC ('CREATE SCHEMA gold')
GO

CREATE TABLE gold.kpi_daily_summary (
    kpi_date DATE NOT NULL,
    hospital_code VARCHAR(20) NOT NULL,
    total_patients INT,
    new_admissions INT,
    discharges INT,
    readmission_count INT,
    readmission_rate_pct DECIMAL(5,2),
    icu_beds_occupied INT,
    icu_beds_total INT,
    icu_utilization_pct DECIMAL(5,2),
    avg_los_days DECIMAL(5,2),
    claims_submitted INT,
    claims_approved INT,
    claims_denied INT,
    denial_rate_pct DECIMAL(5,2),
    revenue_inr DECIMAL(14,2),
    fraud_flags_count INT,
    refreshed_at DATETIME2 DEFAULT GETUTCDATE(),
    pipeline_run_id VARCHAR(200),
    PRIMARY KEY (kpi_date, hospital_code)
);
GO

CREATE TABLE gold.fraud_flags (
    flag_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_id VARCHAR(100) NOT NULL,
    fraud_score INT NOT NULL,
    rule_F1_triggered BIT DEFAULT 0,
    rule_F2_triggered BIT DEFAULT 0,
    rule_F3_triggered BIT DEFAULT 0,
    rule_F4_triggered BIT DEFAULT 0,
    rule_F5_triggered BIT DEFAULT 0,
    flag_date DATE NOT NULL,
    alert_sent BIT DEFAULT 0,
    pipeline_run_id VARCHAR(200),
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

CREATE TABLE gold.lab_tat_summary (
    summary_date DATE NOT NULL,
    hospital_code VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL,
    total_tests INT,
    avg_tat_hours DECIMAL(6,2),
    p95_tat_hours DECIMAL(6,2),
    sla_breaches INT,
    critical_values_flagged INT,
    PRIMARY KEY (summary_date, hospital_code, order_type)
);
GO

CREATE TABLE gold.pharmacy_inventory_alerts (
    alert_date DATE NOT NULL,
    hospital_code VARCHAR(20) NOT NULL,
    drug_id VARCHAR(50) NOT NULL,
    drug_name VARCHAR(200),
    current_stock INT,
    avg_daily_consumption DECIMAL(8,2),
    days_of_stock_remaining DECIMAL(6,1),
    alert_type VARCHAR(30),
    pipeline_run_id VARCHAR(200),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    PRIMARY KEY (alert_date, hospital_code, drug_id)
);
GO
PRINT 'Gold tables created.';
GO
