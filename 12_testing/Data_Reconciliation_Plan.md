# Data Reconciliation
Daily automated check:
`Count(Bronze S1 Patients) == Count(Silver dim_patient where eff_start_date = today)`
If difference > 0, alert DE team.