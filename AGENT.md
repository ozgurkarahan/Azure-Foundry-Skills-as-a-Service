# Foundry Skills

## Overview

Runtime-extensible prompt agent on Azure AI Foundry. Skills are `.md` files stored in Azure Blob Storage, loaded dynamically via a **Skills MCP Server** (two-hop pattern). Adding a new skill = upload a `.md` file to blob. Zero redeployment.

Pattern: [[skills-as-a-service]]

## Architecture

```
User → Foundry PromptAgent (gpt-4o + MCPTool)
         │
         ├─ mcp_list_tools → discovers read_file, list_files, write_file
         │
         ├─ read_file("foundry-skills/translate.md")
         │   → APIM (sub 1, validate-jwt + AppInsights)
         │       → Skills MCP Server (Container App, sub 2)
         │           → Azure Blob Storage (DefaultAzureCredential)
         │           ← returns FULL skill file (not chunks)
         │
         └─ Agent follows skill instructions exactly
```

**Azure resources:**
- AI Services: `s2-oz-ai-projects` (Sweden Central, sub 2, no hub)
- Project: `s2-oz-ai-proj`
- Model: `gpt-4o` (GlobalStandard)
- MCP Server: `ca-skills-mcp` (Container App, sub 2)
- Storage: `stfoundryskills` / container `skills`
- APIM: `apim-sf-mcp-obo` (sub 1, StandardV2)
- AppInsights: `appi-sf-mcp-obo` (sub 1)
- Auth: UserEntraToken connection → APIM validate-jwt

## Key Paths

| Path | Purpose |
|------|---------|
| `src/mcp_server/server.py` | FastMCP server: read_file, list_files, write_file |
| `src/mcp_server/blob_client.py` | Azure Blob Storage client |
| `src/mcp_server/config.py` | MCP server config |
| `src/agent/create_agent.py` | Create/update PromptAgent with MCPTool |
| `src/agent/upload_skills.py` | Upload skill .md files to Azure Blob Storage |
| `src/agent/system_prompt.py` | System prompt (registry table + two-hop instructions) |
| `src/agent/config.py` | Agent config (endpoint, model, name) |
| `skills/*.md` | Skill files (registry + individual skills) |
| `tests/test_e2e.py` | 11 E2E tests (keyword assertions) |
| `tests/test_eval.py` | 5 LLM-as-judge eval cases (format, hallucination, routing) |
| `tests/inspect_traces.py` | Inspect file_search/mcp_call traces in responses |
| `scripts/postprovision.py` | azd post-provision hook: upload skills + create agent |
| `Dockerfile` | Container image for MCP server |
| `azure.yaml` | Azure Developer CLI (azd) configuration |

