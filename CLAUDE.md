# AI Agent Instructions

## Project
Foundry Skills — runtime-extensible prompt agent with Skills-as-a-Service pattern. See AGENT.md for architecture.

## Conventions
- Follow existing code style and patterns
- Run `python -m tests.test_e2e` before committing
- Keep AGENT.md updated with architecture changes
- Skills follow the format: frontmatter (name, version, tags, dependencies) + Purpose, When to Use, Instructions, Output Format, Dependencies, Rules
- Tool descriptions in `server.py` are mini system prompts — they drive agent behavior
- Errors returned as JSON, never raised as exceptions into the agent
- `DefaultAzureCredential` for all Azure auth — never API keys

## Workflow
- Global workflow rules: `~/projects/memory/agent-config/workflow.md`
- Platform & preferences: `~/projects/memory/agent-config/platform.md`
- Pattern reference: `~/projects/memory/wiki/patterns/skills-as-a-service.md`
