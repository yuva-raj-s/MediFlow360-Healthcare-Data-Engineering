# Enterprise Data Lineage Graph
## MediFlow360 Unified Patient Intelligence

This document visualizes the end-to-end data flow and transformations.

```mermaid
graph LR
    subgraph "Source Systems"
        S1[MySQL HIS]
        S2[REST API]
        S3[SFTP CSV]
        S4[CosmosDB]
        S5[PostgreSQL CDC]
        S6[Excel/SharePoint]
        S7[IoT Hub]
    end

    subgraph "Bronze (Raw/Immutable)"
        B1[(patients)]
        B2[(claims)]
        B3[(lab_results)]
        B4[(vitals)]
    end

    subgraph "Silver (Cleansed/Masked)"
        PII[PII Masking Engine]
        S_P[(dim_patient)]
        S_C[(fact_claims)]
        S_L[(fact_lab_results)]
    end

    subgraph "Gold (Serving/KPIs)"
        G_K[(kpi_daily_summary)]
        G_F[(fraud_alerts_gold)]
    end

    subgraph "Serving Layer"
        SYN[Synapse Dedicated Pool]
        PBI[Power BI Dashboards]
    end

    %% Flow
    S1 & S2 & S3 --> B1
    S3 & S5 --> B3
    S7 --> B4
    
    B1 --> PII --> S_P
    B2 --> S_C
    B3 --> S_L
    
    S_P & S_C & S_L --> G_K
    G_K --> SYN --> PBI
    
    %% Alerting
    B1 & S_C -.-> LA[Logic App Alert Router]
    LA --> Teams[Microsoft Teams]
```

### Transformation Logic Key
- **Bronze → Silver**: Schema enforcement, PII masking (Hashing/Regex), SCD Type 2 application.
* **Silver → Gold**: Business logic application, Cross-entity joins, Aggregations.
* **Gold → Synapse**: PolyBase loading, Hash-distribution for performance.
