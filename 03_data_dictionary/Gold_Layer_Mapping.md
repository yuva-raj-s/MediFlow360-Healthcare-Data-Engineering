# Gold Layer KPIs
- **Readmission Rate**: Count(admissions where days_since_last_discharge <= 30) / Count(total_admissions)
- **Denial Rate**: Count(status='DENIED') / Count(total_claims)
- **TAT (Turnaround Time)**: AVG(result_released_ts - specimen_collected_ts)