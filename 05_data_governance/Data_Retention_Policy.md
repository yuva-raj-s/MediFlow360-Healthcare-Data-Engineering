# Data Retention Policy

| Layer | Storage | Retention Period | Action at Expiry |
|-------|---------|------------------|------------------|
| Raw (SFTP landing) | ADLS Blob | 14 days | Soft Delete |
| Bronze | ADLS Parquet | 7 years | Move to Archive tier after 3 yrs. Hard delete at 7 yrs. |
| Silver | ADLS Parquet | 7 years | Same as Bronze. |
| Gold | Azure SQL | 3 years | Aggregations kept for 3 yrs, then archived to ADLS. |
| Audit Logs | Azure SQL | 10 years | Maintained for legal/compliance. |