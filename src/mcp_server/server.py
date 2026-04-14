"""Skills MCP Server — read_file, list_files, write_file against Azure Blob Storage.

A universal Skills-as-a-Service MCP server. Any Foundry agent can connect
to load skill files dynamically via the two-hop discovery pattern:
  1. read_file("registry.md") → skill catalog
  2. read_file("translate.md") → full skill instructions

Blob layout:
  skills-container/
  ├── {agent-name}/           # Agent-scoped skills
  │   ├── registry.md
  │   └── *.md
  └── _shared/                # Skills available to all agents
      ├── summarize.md
      └── translate.md

Usage:
    STORAGE_ACCOUNT=myaccount python -m src.mcp_server.server
"""

import json

from fastmcp import FastMCP

from src.mcp_server.blob_client import read_blob, write_blob, list_blobs
from src.mcp_server.config import MCP_HOST, MCP_PORT

mcp = FastMCP(
    "Skills MCP Server",
    instructions="Provides read/write access to skill files stored in Azure Blob Storage.",
)


@mcp.tool()
def read_file(path: str) -> str:
    """Read a skill file from the skill store.

    Use this tool to load skill instructions. The file content is returned
    as plain text (usually markdown). Always read the full file — it contains
    the complete instructions you must follow.

    Common paths:
    - "registry.md" — lists all available skills with descriptions
    - "{skill-name}.md" — full instructions for a specific skill
    - "_shared/{skill-name}.md" — shared skills available to all agents

    Args:
        path: Path to the file in the skill store (e.g., "registry.md", "translate.md").

    Returns:
        File content as plain text. Returns a JSON error if the file is not found.
    """
    try:
        content = read_blob(path)
        return content
    except FileNotFoundError:
        return json.dumps({"error": "file_not_found", "path": path})
    except Exception as e:
        return json.dumps({"error": "read_failed", "path": path, "detail": str(e)})


@mcp.tool()
def list_files(prefix: str = "") -> str:
    """List available skill files in the skill store.

    Use this tool to discover what skills are available when the registry
    file is missing or you need to browse the store. Returns a JSON array
    of file names and sizes.

    Args:
        prefix: Optional prefix to filter files (e.g., "_shared/" to list shared skills).
                Leave empty to list all files.

    Returns:
        JSON array of {name, size} objects.
    """
    try:
        files = list_blobs(prefix)
        return json.dumps(files)
    except Exception as e:
        return json.dumps({"error": "list_failed", "prefix": prefix, "detail": str(e)})


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write agent output to the skill store.

    Use this tool to save agent-generated content (reports, summaries,
    translations) to persistent storage. Do NOT use this to modify skill
    files — those are managed externally.

    Args:
        path: Path where the file should be written (e.g., "output/report.md").
        content: The text content to write.

    Returns:
        JSON confirmation with bytes written, or error details.
    """
    try:
        size = write_blob(path, content)
        return json.dumps({"success": True, "path": path, "bytes_written": size})
    except Exception as e:
        return json.dumps({"error": "write_failed", "path": path, "detail": str(e)})


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=MCP_HOST, port=MCP_PORT)
