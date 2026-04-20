# Foundry Skills

**A Skills-as-a-Service pattern for Azure AI Foundry — extend your AI agent's capabilities at runtime by uploading a markdown file. Zero redeployment.**

## Objective

This project demonstrates a production-ready pattern for building **runtime-extensible AI agents** on Azure AI Foundry. Instead of hard-coding capabilities into your agent, skills are plain `.md` files stored in Azure Blob Storage and loaded on demand through an MCP (Model Context Protocol) server.

**The core idea:** teach your agent new tricks by uploading a markdown file — no code changes, no redeployment, no downtime.

### What You'll Find Here

- **Skills-as-a-Service pattern** — a reusable architecture where agent capabilities live outside the codebase as versioned markdown files
- **MCP Server** — a FastMCP server (deployed as a Container App behind API Management) that exposes blob storage operations as tools the agent can call
- **Two-hop discovery** — the agent reads a skill registry to know *what* it can do, then fetches the full skill file to know *how* to do it
- **End-to-end testing** — keyword-based E2E tests and LLM-as-judge evaluations to validate agent behavior
- **Infrastructure as Code** — Bicep templates and deployment scripts for the full Azure stack

### Why This Pattern?

| Traditional Agents | Skills-as-a-Service |
|---|---|
| Capabilities baked into code | Capabilities stored as markdown files |
| Redeploy to add features | Upload a `.md` file to add features |
| Monolithic system prompt | Modular skills loaded on demand |
| Hard to version/audit | Each skill is a versioned blob |
| Tight coupling | Loose coupling via MCP |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment — copy sample and fill in your values
cp .env.sample .env

# Required environment variables (edit .env or export directly)
export PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project>"
export MCP_SERVER_URL="https://<apim>.azure-api.net/skills-mcp/mcp"
export STORAGE_ACCOUNT="<your-storage-account>"
# Optional (defaults shown):
# export MODEL_DEPLOYMENT="gpt-4o"
# export AGENT_NAME="foundry-skills"
# export SKILLS_CONTAINER="skills"

# Upload skill files to Azure Blob Storage
python -m src.agent.upload_skills

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
export STORAGE_ACCOUNT="<your-storage-account>"
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
2. Upload to blob: `python -m src.agent.upload_skills` (uploads all files in `skills/` to the configured storage account)
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
│   │   └── config.py           # Server config (STORAGE_ACCOUNT, MCP_HOST, MCP_PORT)
│   └── agent/
│       ├── create_agent.py     # Create/update agent with MCPTool
│       ├── upload_skills.py    # Upload skill .md files to Azure Blob Storage
│       ├── system_prompt.py    # System prompt (registry + two-hop pattern)
│       ├── test_agent.py       # Test agent invocation
│       └── config.py           # Agent config (endpoint, model, name)
├── skills/
│   ├── registry.md             # Skill catalog (human reference)
│   ├── summarize.md            # Summarization skill
│   ├── translate.md            # Translation skill
│   └── analyze-sentiment.md    # Sentiment analysis skill
├── tests/
│   ├── test_e2e.py             # 11 E2E tests (keyword assertions)
│   ├── test_eval.py            # 5 LLM-as-judge eval cases
│   └── inspect_traces.py      # MCP call trace inspector
├── scripts/
│   └── postprovision.py        # azd post-provision hook (upload skills + create agent)
├── infra/                      # Bicep infrastructure templates
├── Dockerfile                  # MCP server container image
├── azure.yaml                  # Azure Developer CLI (azd) configuration
├── requirements.txt
└── .env.sample
```

## Prerequisites

- Azure subscription with AI Services + Foundry project (no hub)
- `gpt-4o` model deployed
- Storage account with blob container for skills
- APIM instance (for auth + logging)
- Python 3.11+
- `azure-ai-projects`, `azure-identity`, `azure-storage-blob`, `fastmcp`, `python-dotenv`
