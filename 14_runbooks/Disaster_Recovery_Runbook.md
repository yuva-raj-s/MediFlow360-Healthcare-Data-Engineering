# DR Runbook
See `11_infrastructure/DR_Plan.md` for architecture strategy.
Execute `13_cicd/Deploy_Instructions.md` to rebuild ADF.
Run `08_sql_scripts/dml/02_truncate_all_tables_dev.sql` (modified for prod) to clean slate before historical replay.