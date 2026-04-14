"""Configuration for the Skills MCP server."""

import os

# Azure Blob Storage
STORAGE_ACCOUNT = os.environ.get("STORAGE_ACCOUNT", "")
SKILLS_CONTAINER = os.environ.get("SKILLS_CONTAINER", "skills")

# Server
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))
