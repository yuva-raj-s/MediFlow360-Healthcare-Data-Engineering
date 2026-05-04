# Incremental Load Patterns

1. **Watermark (Database)**: S1 MySQL, S4 CosmosDB. Read `updated_at` > last watermark.
2. **Watermark (API)**: S2 Claims. Pass `?last_modified=YYYY-MM-DD` to API endpoint.
3. **Event-Based**: S3 LIS. ADF Event Trigger fires on Blob Creation in `/landing/sftp/`.
4. **CDC**: S5 PostgreSQL. Logical replication WAL logs via `pgoutput` plugin.
5. **Micro-Batch**: S7 IoT Hub. 5-minute tumbling windows via ADF.