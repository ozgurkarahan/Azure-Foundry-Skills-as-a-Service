// Container App Environment + Skills MCP Server Container App

param envName string
param appName string
param location string
param image string
param acrLoginServer string
param acrName string
param storageAccountName string
param skillsContainerName string = 'skills'

@secure()
@description('ACR admin password (pass at deploy time)')
param acrPassword string = ''

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${envName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: acrLoginServer
          username: acrName
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acrPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'skills-mcp'
          image: image
          env: [
            {
              name: 'STORAGE_ACCOUNT'
              value: storageAccountName
            }
            {
              name: 'SKILLS_CONTAINER'
              value: skillsContainerName
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output fqdn string = 'https://${app.properties.configuration.ingress.fqdn}'
output identityPrincipalId string = app.identity.principalId
output appName string = app.name
