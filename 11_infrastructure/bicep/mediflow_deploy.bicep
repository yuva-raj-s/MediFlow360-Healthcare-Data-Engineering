/*
  MediFlow360 Bicep Deployment
  Author: Arjun Patel (DE-002)
  Purpose: Provision core Azure components for the Healthcare Pipeline
*/

param location string = resourceGroup().location
param storageAccountName string = 'stmediflow360${uniqueString(resourceGroup().id)}'
param sqlServerName string = 'sql-mediflow360-${uniqueString(resourceGroup().id)}'

// 1. Storage Account (ADLS Gen2)
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    accessTier: 'Hot'
  }
}

// 2. Azure SQL Server
resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: 'sqladmin'
    administratorLoginPassword: 'ComplexPassword123!'
  }
}

// 3. Data Factory
resource adf 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: 'adf-mediflow360-prod'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
}

// 4. Databricks Workspace
resource databricks 'Microsoft.Databricks/workspaces@2023-02-01' = {
  name: 'dbw-mediflow360-prod'
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', 'rg-mediflow360-managed')
  }
}
