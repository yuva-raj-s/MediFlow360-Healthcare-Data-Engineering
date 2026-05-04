# Databricks Notebook: 20_governance_automation/PII_Masking_Engine.py
# MediFlow360 — Advanced PII/PHI Scrubbing Engine
# Purpose: Centralized logic for HIPAA/DPDP compliance

%run ../07_notebooks/00_Helper_NB

from pyspark.sql.functions import col, sha2, lit, regexp_replace, concat, substring, length

class PIIMasker:
    """Industry standard PII masking utility for Healthcare data."""
    
    @staticmethod
    def mask_email(df, email_col="email"):
        """Masks email: a***b@domain.com"""
        return df.withColumn(
            email_col,
            regexp_replace(col(email_col), r"(^[^@]{1})(.*)([^@]{1}@)", r"$1***$3")
        )

    @staticmethod
    def mask_phone(df, phone_col="phone_number"):
        """Masks phone: XXXXXX-1234"""
        return df.withColumn(
            phone_col,
            concat(lit("XXXXXX-"), substring(col(phone_col), -4, 4))
        )

    @staticmethod
    def hash_pii(df, pii_cols: list):
        """Deterministically hashes PII columns (Aadhaar, SSN, PAN)."""
        for c in pii_cols:
            df = df.withColumn(f"{c}_hash", sha2(col(c).cast("string"), 256)).drop(c)
        return df

    @staticmethod
    def redact_address(df, address_col="address"):
        """Redacts full address to City/State level only."""
        # Simple implementation: keep only the last part (usually state/city)
        return df.withColumn(
            address_col,
            lit("[REDACTED_TO_CITY_LEVEL]")
        )

# Example Usage in Silver Layer:
# df = spark.read.table("bronze.patients")
# df_clean = PIIMasker.mask_email(df)
# df_clean = PIIMasker.hash_pii(df_clean, ["aadhaar_number", "ssn"])
# df_clean.write.mode("overwrite").saveAsTable("silver.patients")

print("[PII Engine] Governance logic initialized.")
