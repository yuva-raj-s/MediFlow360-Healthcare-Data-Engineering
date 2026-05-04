# Comprehensive Data Dictionary
Refer to `Source_to_Bronze_Mapping.md` for raw ingress.
**Silver Layer:**
- `dim_patient` (PK: `patient_sk`, NK: `global_patient_id`)
- `dim_provider` (PK: `provider_sk`)
- `fact_claims` (PK: `claim_sk`, FK: `patient_sk`, `provider_sk`)

**Gold Layer:**
- `kpi_daily_summary` (Aggregated at hospital + date level)
- `fraud_flags` (Filter of fact_claims where fraud_score >= 5)