# Manual Deployment Instructions
If CI/CD fails, follow these steps:
1. Export ADF ARM template from ADF UX.
2. Go to Azure Portal -> Deploy a custom template.
3. Upload template, select resource group, deploy.
4. For Databricks: Export notebooks as `.dbc` archive, import into target workspace.