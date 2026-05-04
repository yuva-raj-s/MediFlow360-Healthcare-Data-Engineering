# Masking Rules
Defines specific regex/logic used in `00_Helper_NB.py`.

- **Aadhaar**: `sha2(col("aadhaar_number").cast(StringType()), 256)`
- **Phone**: `regexp_replace(col("phone_number"), r"^\d{6}", "XXXXXX")`
- **Email**: Splitting at `@`. Example: `sXXXXr@mrhs.in`
- **Credit Card** (Future scope): `regexp_replace(col("cc"), r"\d{12}", "XXXX-XXXX-XXXX-")`