"""Create or update the Foundry Skills agent with FileSearchTool + vector store."""

import sys
import time

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FileSearchTool,
    PromptAgentDefinition,
)

from src.agent.config import PROJECT_ENDPOINT, MODEL_DEPLOYMENT, AGENT_NAME
from src.agent.system_prompt import SYSTEM_PROMPT
from src.agent.upload_skills import get_blob_uri


def create_vector_store(client: AIProjectClient, store_name: str = "skills-store", force_recreate: bool = False) -> str:
    """Create a vector store and upload skill files to it.

    Uploads only skill files (excludes registry.md since registry
    is embedded in the system prompt).

    Args:
        client: AIProjectClient instance.
        store_name: Name for the vector store.
        force_recreate: If True, delete existing store and recreate.

    Returns:
        vector store ID.
    """
    openai = client.get_openai_client()

    # Check for existing vector store
    existing_stores = openai.vector_stores.list()
    for store in existing_stores:
        if store.name == store_name:
            if force_recreate:
                print(f"Deleting existing vector store: {store.id}")
                openai.vector_stores.delete(store.id)
                break
            else:
                print(f"Found existing vector store: {store.id} ({store.name})")
                return store.id

    # Upload skill files via OpenAI files API (exclude registry.md)
    import os
    import glob
    from src.agent.config import SKILLS_DIR

    skills_path = os.path.abspath(SKILLS_DIR)
    md_files = glob.glob(os.path.join(skills_path, "**", "*.md"), recursive=True)
    # Exclude registry.md — it's embedded in the system prompt
    md_files = [f for f in md_files if os.path.basename(f) != "registry.md"]

    file_ids = []
    for filepath in md_files:
        with open(filepath, "rb") as f:
            uploaded = openai.files.create(file=f, purpose="assistants")
            file_ids.append(uploaded.id)
            print(f"  Uploaded file: {os.path.basename(filepath)} -> {uploaded.id}")

    # Create vector store with skill files only
    vector_store = openai.vector_stores.create(
        name=store_name,
        file_ids=file_ids,
    )
    print(f"Created vector store: {vector_store.id} ({vector_store.name}) with {len(file_ids)} files")

    # Wait for indexing
    while True:
        store_status = openai.vector_stores.retrieve(vector_store.id)
        counts = store_status.file_counts
        if counts.in_progress == 0:
            print(f"  Indexing complete: {counts.completed} completed, {counts.failed} failed")
            break
        print(f"  Indexing in progress: {counts.in_progress} remaining...")
        time.sleep(2)

    return vector_store.id


def create_agent(vector_store_id: str = None, force_recreate: bool = False):
    """Create or update the Foundry Skills prompt agent.

    Args:
        vector_store_id: ID of the vector store containing skill files.
                         If None, creates one from local skill files.
        force_recreate: If True, recreate the vector store from scratch.
    """
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    # Create vector store if not provided
    if not vector_store_id:
        vector_store_id = create_vector_store(client, force_recreate=force_recreate)

    # Build the FileSearchTool
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store_id])

    # Create the agent definition
    definition = PromptAgentDefinition(
        model=MODEL_DEPLOYMENT,
        instructions=SYSTEM_PROMPT,
        tools=[file_search_tool],
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
        description="Runtime-extensible prompt agent that loads skills from file search.",
    )

    print(f"\nAgent created successfully:")
    print(f"  Name: {AGENT_NAME}")
    print(f"  Model: {MODEL_DEPLOYMENT}")
    print(f"  Vector Store: {vector_store_id}")
    print(f"  Tools: FileSearchTool")

    return agent


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    create_agent(force_recreate=force)
