// AI Services account + Foundry project + model deployment
// Uses the new standalone Foundry model (no hub)

param accountName string
param projectName string
param location string
param modelName string = 'gpt-4o'
param modelVersion string = '2024-11-20'

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: projectName
  location: location
  properties: {}
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: modelName
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

output endpoint string = account.properties.endpoint
output projectEndpoint string = 'https://${accountName}.services.ai.azure.com/api/projects/${projectName}'
output accountId string = account.id
output projectId string = project.id
