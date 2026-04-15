// ============================================================================
// Foundry Skills — Main Bicep orchestration
//
// Deploys: Storage, ACR, Container App, Foundry project, RBAC
// Optionally configures: APIM backend + MCP API (when apimName is provided)
//
// Usage:
//   az deployment group create -g <rg> -f infra/main.bicep \
//     -p location=swedencentral cognitiveAccountName=my-ai projectName=my-proj
// ============================================================================

targetScope = 'resourceGroup'

// --- Required parameters ---
@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Name of the AI Services account (must exist or will be created)')
param cognitiveAccountName string

@description('Name of the Foundry project under the AI Services account')
param projectName string

// --- Optional parameters ---
@description('Suffix for resource names to avoid soft-delete conflicts')
param resourceSuffix string = ''

@description('Container image for the Skills MCP Server (ACR image reference)')
param mcpServerImage string = ''

@description('Name of the existing APIM instance to register the MCP API (leave empty to skip)')
param apimName string = ''

@description('Resource group of the APIM instance (defaults to current RG)')
param apimResourceGroup string = resourceGroup().name

@description('Subscription ID of the APIM instance (defaults to current subscription)')
param apimSubscriptionId string = subscription().subscriptionId

@description('Name of the Container Apps Environment')
param containerAppEnvName string = 'cae-foundry-skills${resourceSuffix}'

@description('Name of the Container App for the MCP server')
param containerAppName string = 'ca-skills-mcp${resourceSuffix}'

@description('Name of the Storage Account for skill files')
param storageAccountName string = 'stfoundryskills${resourceSuffix}'

@description('Name of the ACR for building MCP server images')
param acrName string = 'crfoundryskills${resourceSuffix}'

@description('Name of the blob container for skills')
param skillsContainerName string = 'skills'

@description('Model deployment name')
param modelName string = 'gpt-4o'

@description('Model version')
param modelVersion string = '2024-11-20'

@secure()
@description('ACR admin password for Container App registry auth')
param acrPassword string = ''

// ============================================================================
// Storage Account + skills container
// ============================================================================
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: storageAccountName
    location: location
    containerName: skillsContainerName
  }
}

// ============================================================================
// Container Registry
// ============================================================================
module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: acrName
    location: location
  }
}

// ============================================================================
// AI Services + Foundry Project + Model Deployment
// ============================================================================
module cognitive 'modules/cognitive.bicep' = {
  name: 'cognitive'
  params: {
    accountName: cognitiveAccountName
    projectName: projectName
    location: location
    modelName: modelName
    modelVersion: modelVersion
  }
}

// ============================================================================
// Container App Environment + MCP Server Container App
// ============================================================================
module containerApp 'modules/container-app.bicep' = {
  name: 'containerApp'
  params: {
    envName: containerAppEnvName
    appName: containerAppName
    location: location
    image: mcpServerImage != '' ? mcpServerImage : '${acr.outputs.loginServer}/skills-mcp:latest'
    acrLoginServer: acr.outputs.loginServer
    acrName: acr.outputs.name
    acrPassword: acrPassword
    storageAccountName: storage.outputs.name
    skillsContainerName: skillsContainerName
  }
}

// ============================================================================
// RBAC: Container App managed identity → Storage Blob Data Contributor
// ============================================================================
module rbac 'modules/role-assignment.bicep' = {
  name: 'rbac'
  params: {
    storageAccountName: storage.outputs.name
    principalId: containerApp.outputs.identityPrincipalId
  }
}

// ============================================================================
// APIM: Backend + MCP API (optional, only when apimName is provided)
// ============================================================================
module apim 'modules/apim.bicep' = if (apimName != '') {
  name: 'apim'
  scope: resourceGroup(apimSubscriptionId, apimResourceGroup)
  params: {
    apimName: apimName
    backendUrl: containerApp.outputs.fqdn
    apiPath: 'skills-mcp'
  }
}

// ============================================================================
// Outputs
// ============================================================================
output storageAccountName string = storage.outputs.name
output acrLoginServer string = acr.outputs.loginServer
output containerAppFqdn string = containerApp.outputs.fqdn
output containerAppIdentityPrincipalId string = containerApp.outputs.identityPrincipalId
output cognitiveAccountEndpoint string = cognitive.outputs.endpoint
output projectEndpoint string = cognitive.outputs.projectEndpoint
