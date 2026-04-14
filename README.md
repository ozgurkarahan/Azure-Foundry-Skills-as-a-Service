# Foundry Skills

Runtime-extensible prompt agent on Azure AI Foundry. Skills are markdown files stored in Azure Blob Storage — add a new capability by uploading a `.md` file. Zero redeployment.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PROJECT_ENDPOINT="https://s2-oz-ai-projects.services.ai.azure.com/api/projects/s2-oz-ai-proj"
export MCP_SERVER_URL="https://apim-sf-mcp-obo.azure-api.net/skills-mcp/mcp"
export STORAGE_ACCOUNT="stfoundryskills"

# Create/update the agent
python -m src.agent.create_agent

# Test the agent
python -m src.agent.test_agent "Summarize this text: ..."
python -m src.agent.test_agent "Translate to French: Hello world"
python -m src.agent.test_agent "Analyze the sentiment of: I love this product!"

# Run E2E tests (11 tests)
python -m tests.test_e2e

# Run LLM-as-judge evaluation (5 cases)
python -m tests.test_eval

# Run MCP server locally
export STORAGE_ACCOUNT="stfoundryskills"
python -m src.mcp_server.server
```

## How It Works

1. Skills are `.md` files in Azure Blob Storage (`stfoundryskills/skills`)
2. A **Skills MCP Server** (FastMCP) exposes `read_file`, `list_files`, `write_file` against blob storage
3. The MCP server is deployed as a Container App behind **APIM** (auth + audit logging)
4. A **PromptAgent** is created with `MCPTool` pointing to the APIM endpoint
5. The agent's system prompt contains the **skill registry** (names, descriptions, file paths)
6. When the user asks for help, the agent calls `read_file("foundry-skills/translate.md")` to load the **full** skill file
7. The agent follows the skill's instructions exactly (output format, rules, constraints)

## Adding a New Skill

1. Create a new `.md` file in `skills/` following the existing format (Purpose, When to Use, Instructions, Output Format, Rules)
2. Upload to blob: `az storage blob upload --account-name stfoundryskills --container-name skills --file skills/my-skill.md --name foundry-skills/my-skill.md --auth-mode login`
3. Update the system prompt registry table in `src/agent/system_prompt.py`
4. Re-run `python -m src.agent.create_agent`

## Architecture

```
User → Foundry PromptAgent (gpt-4o + MCPTool)
         │
         ├─ read_file("foundry-skills/translate.md")
         │   → APIM (validate-jwt + AppInsights)
         │       → Skills MCP Server (Container App)
         │           → Azure Blob Storage
         │           ← Full skill file (not chunks)
         │
         └─ Agent follows skill instructions
```

## Project Structure

```
foundry-skills/
├── src/
│   ├── mcp_server/
│   │   ├── server.py           # FastMCP server: read_file, list_files, write_file
│   │   ├── blob_client.py      # Azure Blob Storage client (DefaultAzureCredential)
│   │   └── config.py           # Server config
│   └── agent/
│       ├── create_agent.py     # Create/update agent with MCPTool
│       ├── system_prompt.py    # System prompt (registry + two-hop pattern)
│       ├── test_agent.py       # Test agent invocation
│       └── config.py           # Agent config
├── skills/
│   ├── registry.md             # Skill catalog (human reference)
│   ├── summarize.md            # Summarization skill
│   ├── translate.md            # Translation skill
│   └── analyze-sentiment.md    # Sentiment analysis skill
├── tests/
│   ├── test_e2e.py             # 11 E2E tests (keyword assertions)
│   ├── test_eval.py            # 5 LLM-as-judge eval cases
│   └── inspect_traces.py      # MCP call trace inspector
├── Dockerfile                  # MCP server container image
├── requirements.txt
└── .env.sample
```

## Prerequisites

- Azure subscription with AI Services + Foundry project (no hub)
- `gpt-4o` model deployed
- Storage account with blob container for skills
- APIM instance (for auth + logging)
- Python 3.11+
- `azure-ai-projects`, `azure-identity`, `azure-storage-blob`, `fastmcp`
