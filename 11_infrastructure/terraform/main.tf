# Terraform Infrastructure for MediFlow360
# Standard Healthcare Data Engineering Stack

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-mediflow360-prod"
  location = "East US"
}

# ADLS Gen2 Storage
resource "azurerm_storage_account" "adls" {
  name                     = "stmediflow360prod"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true # Critical for Databricks/ADLS
}

resource "azurerm_storage_data_lake_gen2_filesystem" "container" {
  name               = "mediflow360"
  storage_account_id = azurerm_storage_account.adls.id
}

# Azure SQL for Metadata/Audit
resource "azurerm_mssql_server" "sql" {
  name                         = "sql-mediflow360-prod"
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = azurerm_resource_group.rg.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = "ComplexPassword123!" # In real world, use KeyVault
}

resource "azurerm_mssql_database" "db" {
  name      = "sqldb-mediflow360"
  server_id = azurerm_mssql_server.sql.id
  sku_name  = "Basic" # Free trial friendly
}

# Data Factory
resource "azurerm_data_factory" "adf" {
  name                = "adf-mediflow360-prod"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# Key Vault
resource "azurerm_key_vault" "kv" {
  name                = "kv-mediflow360-prod"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = "00000000-0000-0000-0000-000000000000" # Placeholder
  sku_name            = "standard"
}
