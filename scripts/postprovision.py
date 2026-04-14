"""Postprovision script: upload skills to blob + create/update Foundry agent.

Run after `azd provision` to:
1. Upload skill .md files to Azure Blob Storage
2. Create the Foundry agent with MCPTool pointing to the MCP server
"""

import os
import sys
import glob

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient


def upload_skills():
    """Upload skill files to Azure Blob Storage."""
    storage_account = os.environ.get("STORAGE_ACCOUNT", "")
    container_name = os.environ.get("SKILLS_CONTAINER", "skills")
    agent_name = os.environ.get("AGENT_NAME", "foundry-skills")

    if not storage_account:
        print("STORAGE_ACCOUNT not set, skipping skill upload")
        return

    blob_url = f"https://{storage_account}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    client = ContainerClient(
        account_url=blob_url,
        container_name=container_name,
        credential=credential,
    )

    skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills")
    skills_path = os.path.abspath(skills_dir)
    md_files = glob.glob(os.path.join(skills_path, "**", "*.md"), recursive=True)

    print(f"\nUploading skills to {storage_account}/{container_name}...")
    for filepath in md_files:
        filename = os.path.basename(filepath)
        for prefix in [f"{agent_name}/", "_shared/"]:
            blob_name = f"{prefix}{filename}"
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            client.upload_blob(name=blob_name, data=content, overwrite=True)
            print(f"  {blob_name}")

    print(f"Uploaded {len(md_files)} skills to both {agent_name}/ and _shared/")


def create_agent():
    """Create the Foundry agent with MCPTool."""
    print("\nCreating Foundry agent...")
    from src.agent.create_agent import create_agent as _create_agent
    _create_agent()


if __name__ == "__main__":
    upload_skills()
    create_agent()
    print("\nPostprovision complete!")
