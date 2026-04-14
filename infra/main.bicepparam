using 'main.bicep'

param location = readEnvironmentVariable('AZURE_LOCATION', 'swedencentral')
param cognitiveAccountName = readEnvironmentVariable('COGNITIVE_ACCOUNT_NAME', 's2-oz-ai-projects')
param projectName = readEnvironmentVariable('FOUNDRY_PROJECT_NAME', 's2-oz-ai-proj')
param resourceSuffix = readEnvironmentVariable('RESOURCE_SUFFIX', '')
param storageAccountName = readEnvironmentVariable('STORAGE_ACCOUNT', 'stfoundryskills')
param acrName = readEnvironmentVariable('ACR_NAME', 'crfoundryskills')
param mcpServerImage = readEnvironmentVariable('MCP_SERVER_IMAGE', '')
param modelName = readEnvironmentVariable('MODEL_NAME', 'gpt-4o')
param modelVersion = readEnvironmentVariable('MODEL_VERSION', '2024-11-20')

// APIM integration (optional — set these to register the MCP API in an existing APIM)
param apimName = readEnvironmentVariable('APIM_NAME', '')
param apimResourceGroup = readEnvironmentVariable('APIM_RESOURCE_GROUP', '')
param apimSubscriptionId = readEnvironmentVariable('APIM_SUBSCRIPTION_ID', '')
