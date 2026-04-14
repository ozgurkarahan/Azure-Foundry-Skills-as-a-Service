"""Create or update the Foundry Skills agent with MCPTool (Skills MCP Server)."""

import os
import sys

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    MCPTool,
    PromptAgentDefinition,
)

from src.agent.config import PROJECT_ENDPOINT, MODEL_DEPLOYMENT, AGENT_NAME
from src.agent.system_prompt import SYSTEM_PROMPT

# MCP server URL (Container App)
MCP_SERVER_URL = os.environ.get(
    "MCP_SERVER_URL",
    "https://ca-skills-mcp.greenrock-9f8cee2b.swedencentral.azurecontainerapps.io/mcp",
)


def create_agent():
    """Create or update the Foundry Skills prompt agent with MCPTool."""
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    # Build the MCPTool pointing to the Skills MCP Server
    mcp_tool = MCPTool(
        server_label="skills_mcp",
        server_url=MCP_SERVER_URL,
        require_approval="never",
    )

    # Create the agent definition
    definition = PromptAgentDefinition(
        model=MODEL_DEPLOYMENT,
        instructions=SYSTEM_PROMPT,
        tools=[mcp_tool],
        temperature=0.3,
    )

    # Create or update agent version
    try:
        existing = client.agents.get(AGENT_NAME)
        print(f"Agent '{AGENT_NAME}' already exists, creating new version...")
    except Exception:
        print(f"Creating new agent: {AGENT_NAME}")

    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=definition,
        description="Runtime-extensible prompt agent that loads skills via MCP read_file (two-hop pattern).",
    )

    print(f"\nAgent created successfully:")
    print(f"  Name: {AGENT_NAME}")
    print(f"  Model: {MODEL_DEPLOYMENT}")
    print(f"  MCP Server: {MCP_SERVER_URL}")
    print(f"  Tools: MCPTool (read_file, list_files, write_file)")

    return agent


if __name__ == "__main__":
    create_agent()
