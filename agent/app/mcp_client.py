"""Minimal MCP client: connect to a stdio tool server, list tools, call one."""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVERS = {  # edit to add servers
    "sqlite": StdioServerParameters(command="uvx", args=["mcp-server-sqlite", "--db-path", "/tmp/apex.db"]),
    "files": StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/data"]),
}

async def call_tool(server: str, tool: str, args: dict):
    async with stdio_client(SERVERS[server]) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return (await s.call_tool(tool, args)).content

async def list_tools(server: str):
    async with stdio_client(SERVERS[server]) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return [t.name for t in (await s.list_tools()).tools]
