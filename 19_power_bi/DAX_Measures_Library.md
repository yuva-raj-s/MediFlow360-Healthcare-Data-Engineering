# DAX Measure Library

```dax
Readmission_Rate_Pct = 
DIVIDE(
    CALCULATE(SUM(fact_admissions[is_readmission])),
    COUNT(fact_admissions[admission_id]),
    0
)

Claims_Denial_Rate = 
DIVIDE(
    CALCULATE(COUNT(fact_claims[claim_id]), fact_claims[status] = "DENIED"),
    COUNT(fact_claims[claim_id]),
    0
)

YTD_Revenue = 
TOTALYTD(SUM(fact_claims[approved_amount]), 'Date'[Date])
```