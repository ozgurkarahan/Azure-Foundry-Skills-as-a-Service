# Lessons Learned

## 2026-04-14 — FileSearchTool loads chunks, not full files
**Mistake:** Used FileSearchTool for skill loading — assumed it would return full files.
**Root cause:** FileSearchTool uses vector search with chunking. For short files (<500 tokens) it works, but for longer skills the instructions get truncated.
**Rule:** For skill instructions that must be followed exactly, use MCP `read_file` (returns full file). FileSearchTool is for RAG-style retrieval, not instruction loading.

## 2026-04-14 — ApiKey connection + MCPTool = HTTP 404
**Mistake:** Created an `ApiKey` Foundry connection and set `project_connection_id` on `MCPTool`.
**Root cause:** Foundry's MCP client changes how it connects when an ApiKey connection is provided, breaking MCP routing. The endpoint returns 404.
**Rule:** For MCPTool auth, use `UserEntraToken` connections. ApiKey connections are NOT compatible with MCPTool.

## 2026-04-14 — authType discriminator required in ARM REST
**Mistake:** Created a Foundry connection via ARM REST without `authType` in the body.
**Root cause:** Foundry ARM API requires the `authType` discriminator property.
**Rule:** Always include `"authType": "UserEntraToken"` (or `"ApiKey"`) in the connection body.

## 2026-04-14 — Registry in system prompt, not in vector store
**Mistake:** Initially put registry.md in the vector store alongside skills — agent searched for everything.
**Root cause:** FileSearchTool returns all files ranked by similarity. No way to say "read this file first, then that one".
**Rule:** Embed the skill registry (catalog table) in the system prompt. The agent knows what skills exist without searching. MCP `read_file` loads only the needed skill.

## 2026-04-14 — APIM body logging breaks MCP SSE
**Mistake:** Default APIM diagnostics log response bodies.
**Root cause:** Response body logging interferes with MCP SSE streaming.
**Rule:** Set body bytes to 0 in APIM diagnostics for MCP APIs.
