"""Azure Blob Storage client for the Skills MCP server."""

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient

from src.mcp_server.config import STORAGE_ACCOUNT, SKILLS_CONTAINER


_container_client = None


def get_container_client() -> ContainerClient:
    """Get or create a singleton ContainerClient for the skills container."""
    global _container_client
    if _container_client is None:
        if not STORAGE_ACCOUNT:
            raise ValueError("STORAGE_ACCOUNT environment variable is required.")
        blob_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        _container_client = ContainerClient(
            account_url=blob_url,
            container_name=SKILLS_CONTAINER,
            credential=credential,
        )
    return _container_client


def read_blob(path: str) -> str:
    """Read a file from blob storage. Returns content or raises FileNotFoundError."""
    client = get_container_client()
    blob = client.get_blob_client(path)
    try:
        data = blob.download_blob()
        return data.readall().decode("utf-8")
    except Exception as e:
        if "BlobNotFound" in str(e) or "404" in str(e):
            raise FileNotFoundError(f"File not found: {path}")
        raise


def write_blob(path: str, content: str) -> int:
    """Write content to blob storage. Returns bytes written."""
    client = get_container_client()
    blob = client.get_blob_client(path)
    data = content.encode("utf-8")
    blob.upload_blob(data, overwrite=True)
    return len(data)


def list_blobs(prefix: str = "") -> list[dict]:
    """List blobs under a prefix. Returns list of {name, size} dicts."""
    client = get_container_client()
    blobs = client.list_blobs(name_starts_with=prefix or None)
    return [{"name": b.name, "size": b.size} for b in blobs]
