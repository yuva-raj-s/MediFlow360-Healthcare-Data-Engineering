# Slowly Changing Dimensions (SCD) Architecture
## MediFlow360 Data Platform
**Document ID:** MRHS-ARCH-008 | **Author:** Kavitha Rajan (DE-003) | **Date:** Jan 18, 2024

To maintain historical accuracy for clinical and financial auditing (NABH compliance), MediFlow360 implements strict SCD strategies in the Silver Medallion layer.

### 1. SCD Type 1: Overwrite
Used for attributes where historical state is irrelevant to analytical outcomes.
* **Target Table:** `silver.dim_provider`
* **Attributes:** `email`, `contact_number`
* **Implementation:** PySpark `MERGE INTO` statement. The existing record is updated in place.
* **Pros:** Simplicity, small storage footprint.

### 2. SCD Type 2: Full History (Row Versioning)
Used for critical clinical and demographic attributes where historical point-in-time analysis is required.
* **Target Table:** `silver.dim_patient`
* **Attributes:** `address_line1`, `insurance_provider`, `primary_care_physician_id`
* **Implementation:** 
  1. Calculate `SHA-256` hash of business keys and tracked columns.
  2. If hash changes: 
     - Update existing row: `is_current = 0`, `eff_end_date = current_timestamp()`.
     - Insert new row: `is_current = 1`, `eff_start_date = current_timestamp()`, `eff_end_date = '9999-12-31'`.
* **Incident Reference:** See **INC-005** for the critical flaw we hit when using the Silver table's `updated_at` column as the watermark for SCD Type 2 incremental loads.

### 3. SCD Type 3: Current & Previous (Columnar)
Used when business users only need to compare the *current* state vs the *immediate previous* state, usually for price tracking.
* **Target Table:** `silver.dim_drug_pricing`
* **Attributes:** `drug_price`
* **Implementation:** 
  1. Identify price change.
  2. Move existing `current_price` to `previous_price` column.
  3. Overwrite `current_price` with new incoming price.
  4. Update `price_effective_date`.

### Technical Execution Notes (Databricks)
SCD operations are performed using Delta Lake's ACID transactions. The `02b_Silver_SCD2_NB.py` notebook handles the complex `MERGE` logic required to simultaneously expire old rows and insert new rows in a single atomic commit.