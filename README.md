# Foundry Skills

Runtime-extensible prompt agent on Azure AI Foundry. Skills are markdown files — add a new capability by uploading a `.md` file.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create the agent (uploads skills + creates vector store + creates agent)
python -m src.agent.create_agent

# Test the agent
python -m src.agent.test_agent "Summarize this text: ..."
python -m src.agent.test_agent "Translate to French: Hello world"
python -m src.agent.test_agent "Analyze the sentiment of: I love this product!"
```

## How It Works

1. Skill files (`.md`) are uploaded to a Foundry vector store via the OpenAI files API
2. A PromptAgent is created with `FileSearchTool` pointing to the vector store
3. When the user asks for help, the agent searches its files for a matching skill
4. The agent follows the skill's instructions exactly (output format, rules, constraints)

## Adding a New Skill

1. Create a new `.md` file in `skills/` following the existing format:
   - Purpose, When to Use, Instructions, Output Format, Rules
2. Update `skills/registry.md` with the new skill entry
3. Re-run `python -m src.agent.create_agent` to update the vector store

## Architecture

```
User → Foundry PromptAgent (gpt-4o + FileSearchTool)
         │
         ├─ Vector store contains skill .md files
         │   → Agent searches semantically for matching skill
         │   ← Returns skill content with instructions
         │
         └─ Agent follows skill instructions to generate response
```

## Project Structure

```
foundry-skills/
├── src/agent/
│   ├── create_agent.py     # Create/update agent + vector store
│   ├── system_prompt.py    # Agent system prompt
│   ├── upload_skills.py    # Upload skills to blob storage
│   ├── test_agent.py       # Test agent invocation
│   └── config.py           # Configuration
├── skills/
│   ├── registry.md         # Skill catalog
│   ├── summarize.md        # Summarization skill
│   ├── translate.md        # Translation skill
│   └── analyze-sentiment.md # Sentiment analysis skill
├── requirements.txt
└── .env.sample
```

## Prerequisites

- Azure subscription with AI Services account + Foundry project
- `gpt-4o` model deployed
- Python 3.11+
- `azure-ai-projects`, `azure-identity`, `azure-storage-blob`
