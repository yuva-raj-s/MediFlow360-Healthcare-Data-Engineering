# CR-001: Add Fraud Detection
**Requestor**: CFO
**Status**: APPROVED | **Implemented**: Sprint 3

**Description**:
Add 5 rule-based fraud scoring checks to Claims processing.
- Rule 1: Same procedure billed >2x in 7 days.
- Rule 2: Amount > 200,000 INR.
- ...
Implement in `04_Anomaly_Detection_NB.py`. Alert immediately if score >= 5.