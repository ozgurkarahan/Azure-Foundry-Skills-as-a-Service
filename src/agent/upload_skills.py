"""Upload skill files to Azure Blob Storage and create/update vector store."""

import os
import glob

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from src.agent.config import STORAGE_ACCOUNT, SKILLS_CONTAINER, SKILLS_DIR


def upload_skills(storage_account: str = None, container: str = None, skills_dir: str = None):
    """Upload all .md files from the skills directory to Azure Blob Storage.

    Args:
        storage_account: Storage account name. Defaults to config.
        container: Container name. Defaults to config.
        skills_dir: Local directory containing skill files. Defaults to config.

    Returns:
        list of uploaded blob names.
    """
    storage_account = storage_account or STORAGE_ACCOUNT
    container = container or SKILLS_CONTAINER
    skills_dir = skills_dir or SKILLS_DIR

    if not storage_account:
        raise ValueError("STORAGE_ACCOUNT is required. Set it in .env or pass as argument.")

    blob_url = f"https://{storage_account}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service = BlobServiceClient(account_url=blob_url, credential=credential)

    container_client = blob_service.get_container_client(container)
    try:
        container_client.create_container()
        print(f"Created container: {container}")
    except Exception:
        print(f"Container already exists: {container}")

    skills_path = os.path.abspath(skills_dir)
    md_files = glob.glob(os.path.join(skills_path, "**", "*.md"), recursive=True)

    uploaded = []
    for filepath in md_files:
        blob_name = os.path.relpath(filepath, skills_path).replace("\\", "/")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        container_client.upload_blob(name=blob_name, data=content, overwrite=True)
        uploaded.append(blob_name)
        print(f"  Uploaded: {blob_name}")

    print(f"\nUploaded {len(uploaded)} skill files to {storage_account}/{container}")
    return uploaded


def get_blob_uri(storage_account: str = None, container: str = None) -> str:
    """Get the Azure Blob Storage URI for the skills container."""
    storage_account = storage_account or STORAGE_ACCOUNT
    container = container or SKILLS_CONTAINER
    return f"https://{storage_account}.blob.core.windows.net/{container}"


if __name__ == "__main__":
    upload_skills()
