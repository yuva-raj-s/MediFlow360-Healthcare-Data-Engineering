# Enterprise Deployment Guide
## MediFlow360 Unified Patient Intelligence Platform

### 🛠️ Infrastructure as Code (IaC) - PREFERRED
The entire platform is automated using Terraform or Bicep.

#### Option A: Terraform (Industry Standard)
1. Navigate to `11_infrastructure/terraform/`.
2. Run `terraform init` to download providers.
3. Run `terraform plan -out=main.tfplan` to review changes.
4. Run `terraform apply main.tfplan` to provision resources.

#### Option B: Azure Bicep
1. Navigate to `11_infrastructure/bicep/`.
2. Run `az deployment group create --resource-group mrhs-rg-prod --template-file mediflow_deploy.bicep`.

### 🚀 Data Orchestration (ADF)
1. Connect ADF to the GitHub repository.
2. In the `13_cicd/` folder, configure `azure-pipelines.yml`.
3. The pipeline will automatically validate the ARM template and publish it to the `adf_publish` branch.

### 📓 Databricks Processing
1. Enable **Databricks Repos** and sync with the `master` branch.
2. The notebooks in `07_notebooks/` will be available as Workspace objects.
3. Configure **Unity Catalog** schemas using the `00_Helper_NB` constants.

### 🛡️ Security Audit
Run the **Notebook Secret Scan** stage in the CI/CD pipeline before any production deployment to ensure zero PII leaks.