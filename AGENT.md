# Foundry Skills

## Overview

Runtime-extensible prompt agent on Azure AI Foundry. Skills are `.md` files loaded dynamically via FileSearchTool + vector store. Adding a new skill = upload a `.md` file, zero redeployment.

## Architecture

```
User → Foundry PromptAgent (gpt-4o)
         │
         ├─ FileSearchTool (vector store backed by skill .md files)
         │   → Searches semantically for matching skill
         │   ← Returns skill instructions
         │
         └─ Agent follows skill instructions to respond
```

**Target:** Azure AI Foundry (new standalone model, no hub)
- AI Services: `s2-oz-ai-projects` (Sweden Central)
- Project: `s2-oz-ai-proj`
- Model: `gpt-4o` (GlobalStandard, 10 TPM)

## Key Paths

| Path | Purpose |
|------|---------|
| `src/agent/create_agent.py` | Create/update agent + vector store |
| `src/agent/system_prompt.py` | Agent system prompt |
| `src/agent/upload_skills.py` | Upload skill files to blob storage |
| `src/agent/test_agent.py` | Test agent invocation |
| `src/agent/config.py` | Configuration (endpoints, model, names) |
| `skills/` | Skill markdown files |
| `skills/registry.md` | Skill catalog |

