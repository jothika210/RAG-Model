"""Week 9 -- a thin adapter that discovers MCP tools at runtime (the real
tools/list RPC) and exposes them generically, so app/agent.py never needs
a hand-added elif branch per tool. Contrast with app/agent_tools.py's
TOOL_DESCRIPTIONS, which is hand-written prose a human wrote in advance --
MCPToolRegistry's prompt block is auto-generated from the server's own
live JSON schema instead.
"""

import asyncio
import logging

from fastmcp import Client

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Connects to one MCP server (a FastMCP instance, a stdio script
    path, or an HTTP URL -- anything fastmcp.Client accepts) and discovers
    its tools at construction time. Tool names, descriptions, and JSON
    schemas all come from the server's live tools/list response -- none
    of it is a Python literal written in advance.
    """

    def __init__(self, server: str):
        self._server = server
        self._tools: dict[str, dict] = {}

    def discover(self) -> dict[str, dict]:
        return asyncio.run(self._discover_async())

    async def _discover_async(self) -> dict[str, dict]:
        client = Client(self._server)
        async with client:
            tools = await client.list_tools()
        self._tools = {
            t.name: {"description": t.description or "", "schema": t.input_schema}
            for t in tools
        }
        logger.info(f"Discovered {len(self._tools)} MCP tools: {list(self._tools)}")
        return self._tools

    def discovered_tool_names(self) -> set[str]:
        return set(self._tools)

    def as_prompt_block(self) -> str:
        """Auto-generates tool-description prose FROM the discovered
        schema -- this is what makes the agent's system prompt reflect
        tools it learned about at runtime, not tools a human wrote about
        in advance.
        """
        if not self._tools:
            return ""
        lines = ["You also have access to these MCP-discovered tools (schemas below came from a live tools/list call, not hand-written):"]
        for name, meta in self._tools.items():
            props = meta["schema"].get("properties", {})
            required = set(meta["schema"].get("required", []))
            arg_descriptions = ", ".join(
                f"{arg}{'*' if arg in required else ''}: {spec.get('description', spec.get('type', 'any'))}"
                for arg, spec in props.items()
            )
            lines.append(f"- {name}({arg_descriptions})\n  {meta['description']}")
        return "\n".join(lines)

    def call(self, name: str, arguments: dict) -> str:
        return asyncio.run(self._call_async(name, arguments))

    async def _call_async(self, name: str, arguments: dict) -> str:
        client = Client(self._server)
        async with client:
            result = await client.call_tool(name, arguments)
        if result.content:
            return result.content[0].text
        return str(result)
