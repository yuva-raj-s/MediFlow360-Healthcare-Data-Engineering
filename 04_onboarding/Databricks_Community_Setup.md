# Databricks Community Edition — Setup Guide
## MediFlow360 | Document ID: MRHS-ONB-003
**Author**: Kavitha Rajan (DE-003) | **Date**: January 16, 2024

---

## Step 1: Create Account

1. Go to: https://www.databricks.com/try-databricks
2. Click **"Get started with Community Edition"** (NOT the Azure trial)
3. Register with your MRHS email: `yourname@mrhs-de.in`
4. Verify email, log in at: https://community.cloud.databricks.com

> ⚠️ Community Edition uses shared compute — no dedicated cluster. This is intentional (free tier).

---

## Step 2: Create Cluster

1. Left sidebar → **Compute** → **Create Compute**
2. Settings:
   - **Cluster Name**: `mrhs-shared-cluster-01`
   - **Databricks Runtime**: 13.3 LTS (Spark 3.4, Scala 2.12)
   - **Node Type**: Default (Community Edition assigns automatically)
   - **Auto Terminate**: ✅ **30 minutes** (MANDATORY — see LOG-002)
3. Click **Create Compute**
4. Wait ~5 minutes for cluster to start

---

## Step 3: Install Libraries

After cluster starts, go to **Cluster → Libraries → Install New**:

```
pypi: azure-keyvault-secrets==4.7.0
pypi: azure-identity==1.15.0
pypi: requests==2.31.0
pypi: pandas==2.0.3
pypi: great-expectations==0.18.12
```

---

## Step 4: Import Notebooks

1. Left sidebar → **Workspace** → **Users** → your username
2. Click three dots → **Import**
3. Import each `.py` file from `/07_notebooks/` in this order:
   - `00_Helper_NB.py` (import first — others depend on it)
   - `01_Bronze_Ingestion_NB.py`
   - `01b_Bronze_CDC_Pharmacy_NB.py`
   - `02_Silver_Transform_NB.py`
   - `02b_Silver_SCD2_NB.py`
   - `02c_Silver_SCD3_NB.py`
   - `03_Gold_Aggregation_NB.py`
   - `04_Anomaly_Detection_NB.py`
   - `05_Data_Quality_NB.py`
   - `06_Alert_Dispatcher_NB.py`
   - `07_Watermark_Manager_NB.py`

---

## Step 5: Configure Secrets (Simulated Key Vault)

In Community Edition, we simulate Key Vault using Databricks Secrets:

```bash
# Run in Databricks CLI (install: pip install databricks-cli)
databricks configure --token  # Enter Community Edition URL + token

# Create secret scope
databricks secrets create-scope --scope mrhs-kv-scope

# Add secrets (values from OPS-001)
databricks secrets put --scope mrhs-kv-scope --key mysql-his-chennai-pwd
databricks secrets put --scope mrhs-kv-scope --key pg-pharmacy-pwd
databricks secrets put --scope mrhs-kv-scope --key adls-account-key
databricks secrets put --scope mrhs-kv-scope --key claims-api-client-secret
```

In notebooks, retrieve as:
```python
pwd = dbutils.secrets.get(scope="mrhs-kv-scope", key="mysql-his-chennai-pwd")
```

---

## Step 6: Verify Setup

Run `00_Helper_NB.py` — it performs a self-check:
- ✅ Spark version check
- ✅ Secret scope connectivity
- ✅ ADLS mount point test
- ✅ Audit table write test

If all 4 checks pass, you're ready!

---

## ADLS Mount (Run Once)

```python
# In 00_Helper_NB.py — mount command already included
storage_account = "mrhsadlsprod"
container = "mediflow360"
account_key = dbutils.secrets.get(scope="mrhs-kv-scope", key="adls-account-key")

dbutils.fs.mount(
    source=f"wasbs://{container}@{storage_account}.blob.core.windows.net",
    mount_point="/mnt/mediflow360",
    extra_configs={f"fs.azure.account.key.{storage_account}.blob.core.windows.net": account_key}
)
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Cluster terminates mid-run | Community Edition has session limits — break into smaller runs |
| `ModuleNotFoundError: azure.keyvault` | Re-install library after cluster restart |
| `Mount already exists` error | Run `dbutils.fs.unmount("/mnt/mediflow360")` first |
| Slow execution | Community Edition is shared — run during off-peak hours (early morning IST) |

---
*MRHS Confidential | Databricks Setup Guide | v1.0*
