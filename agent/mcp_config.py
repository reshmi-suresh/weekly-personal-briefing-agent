"""MCP server definitions for Gmail, Google Calendar, and Notion."""

MCP_BETA = "mcp-client-2025-11-20"

MCP_SERVERS = [
    {"type": "url", "url": "https://gmailmcp.googleapis.com/mcp/v1", "name": "gmail"},
    {
        "type": "url",
        "url": "https://calendarmcp.googleapis.com/mcp/v1",
        "name": "google-calendar",
    },
    {"type": "url", "url": "https://mcp.notion.com/mcp", "name": "notion"},
]


def mcp_tools(server_names: list[str] | None = None) -> list[dict]:
    """Build MCPToolset entries for the given server names (default: all)."""
    names = server_names or [s["name"] for s in MCP_SERVERS]
    return [{"type": "mcp_toolset", "mcp_server_name": name} for name in names]
