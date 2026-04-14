// APIM Backend + MCP API for Skills MCP Server
// Deployed cross-subscription when APIM is on a different sub
// Uses api-version 2025-03-01-preview for MCP type support

param apimName string
param backendUrl string
param apiPath string = 'skills-mcp'

resource apim 'Microsoft.ApiManagement/service@2024-06-01-preview' existing = {
  name: apimName
}

resource backend 'Microsoft.ApiManagement/service/backends@2024-06-01-preview' = {
  parent: apim
  name: '${apiPath}-backend'
  properties: {
    url: backendUrl
    protocol: 'http'
    description: 'Skills MCP Server (Container App)'
  }
}

// BCP037 warnings for MCP properties are expected and safe to ignore
#disable-next-line BCP037
resource mcpApi 'Microsoft.ApiManagement/service/apis@2025-03-01-preview' = {
  parent: apim
  name: apiPath
  properties: {
    displayName: 'Skills MCP Server'
    path: apiPath
    type: 'mcp'
    subscriptionRequired: false
    protocols: [
      'https'
    ]
    backendId: backend.name
    #disable-next-line BCP037
    mcpProperties: {
      endpoints: {
        mcp: {
          uriTemplate: '/mcp'
        }
      }
    }
  }
}

// API-level policy: validate-jwt + identity extraction + audit headers
resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2024-06-01-preview' = {
  parent: mcpApi
  name: 'policy'
  properties: {
    format: 'xml'
    value: '''
<policies>
    <inbound>
        <base />
        <validate-jwt header-name="Authorization" failed-validation-httpcode="401" failed-validation-error-message="Invalid Azure AD token" require-scheme="Bearer" output-token-variable-name="jwt">
            <openid-config url="https://login.microsoftonline.com/{{TenantId}}/v2.0/.well-known/openid-configuration" />
            <audiences>
                <audience>https://ai.azure.com</audience>
                <audience>https://cognitiveservices.azure.com</audience>
            </audiences>
            <issuers>
                <issuer>https://login.microsoftonline.com/{{TenantId}}/v2.0</issuer>
                <issuer>https://sts.windows.net/{{TenantId}}/</issuer>
            </issuers>
        </validate-jwt>
        <set-variable name="userId" value="@(((Jwt)context.Variables[&quot;jwt&quot;]).Claims.GetValueOrDefault(&quot;preferred_username&quot;, ((Jwt)context.Variables[&quot;jwt&quot;]).Claims.GetValueOrDefault(&quot;upn&quot;, ((Jwt)context.Variables[&quot;jwt&quot;]).Claims.GetValueOrDefault(&quot;unique_name&quot;, &quot;unknown&quot;))))" />
        <set-header name="X-User-Id" exists-action="override">
            <value>@((string)context.Variables["userId"])</value>
        </set-header>
        <set-header name="X-Request-ID" exists-action="skip">
            <value>@(context.RequestId.ToString())</value>
        </set-header>
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
'''
  }
}
