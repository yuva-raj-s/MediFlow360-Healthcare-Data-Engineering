# Sprint 1 Planning
**Date**: Jan 15, 2024
**Attendees**: Full DE Team, PM

**Goals**:
- Setup Azure Infra.
- Implement Bronze ingestion for S1 (MySQL) and S2 (Claims API).

**Discussion**:
- *Suresh*: "I can get the SHIR VM provisioned by Tuesday."
- *Arjun*: "The Claims API uses OAuth2. ADF handles this natively but we need the Client Secret in Key Vault today."
- *Priya*: "Let's standardize the Bronze PySpark notebook to just hash Aadhaar and add the watermark timestamp. No complex joins yet."