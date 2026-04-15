"""Configuration for the Foundry Skills agent."""

import os

# Azure AI Foundry project endpoint
# Format: https://{account}.services.ai.azure.com/api/projects/{project}
PROJECT_ENDPOINT = os.environ.get(
    "PROJECT_ENDPOINT",
    "https://ai-account-ykihasoqpqobs.services.ai.azure.com/api/projects/ai-project-foundry-skills-test",
)

# Model deployment name (must exist in the AI Services account)
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT", "gpt-4o")

# Agent name in Foundry
AGENT_NAME = os.environ.get("AGENT_NAME", "foundry-skills")

# Azure Blob Storage
STORAGE_ACCOUNT = os.environ.get("STORAGE_ACCOUNT", "")
SKILLS_CONTAINER = os.environ.get("SKILLS_CONTAINER", "skills")

# Local skills directory
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "skills")
