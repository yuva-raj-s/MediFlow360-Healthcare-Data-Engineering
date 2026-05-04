$base = "c:\Users\Yuvaraj s\Desktop\Hobby_Healthcare_Complex"
$dirs = @(
    "00_project_charter",
    "01_business_requirements",
    "02_solution_design",
    "02_solution_design\Architecture_Decision_Records",
    "03_data_dictionary",
    "04_onboarding",
    "05_data_governance",
    "06_source_data\schema_registry",
    "06_source_data\s1_mysql_patients",
    "06_source_data\s2_rest_api_claims",
    "06_source_data\s3_sftp_lab_results",
    "06_source_data\s4_mongodb_appointments",
    "06_source_data\s5_postgres_pharmacy",
    "06_source_data\s6_sharepoint_excel",
    "06_source_data\s7_iothub_vitals",
    "07_notebooks",
    "08_sql_scripts\ddl",
    "08_sql_scripts\dml",
    "08_sql_scripts\monitoring",
    "09_adf_pipelines\pipeline_configs",
    "09_adf_pipelines\linked_services",
    "09_adf_pipelines\integration_runtimes",
    "09_adf_pipelines\triggers",
    "10_alerting",
    "11_infrastructure",
    "12_testing",
    "13_cicd",
    "14_runbooks",
    "15_incidents_and_struggles",
    "16_change_requests",
    "17_meeting_notes",
    "18_sprint_artifacts",
    "19_power_bi"
)
foreach ($d in $dirs) {
    $path = Join-Path $base $d
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    Write-Host "Created: $d"
}
Write-Host "All directories created successfully."
