"""Week 9 -- proof that a genuinely DIFFERENT client/agent (not
app/agent.py, not app/mcp_client.py's stdio-subprocess pattern) can
discover and call this project's own MCP server. Connects over HTTP to
a separately-started server process:

    python mcp_server/hris_server.py --http --port 8765

...then, in a second terminal:

    python scripts/demo_external_mcp_client.py

This script imports nothing from app/ except what's needed to print a
readable demo -- it does not reuse app/mcp_client.py's MCPToolRegistry,
specifically so it reads as an independent client, not something
secretly coupled to this project's own agent code.
"""

import asyncio
import sys

from fastmcp import Client

SERVER_URL = "http://127.0.0.1:8765/mcp"


async def main() -> None:
    print(f"Connecting to {SERVER_URL} as an independent client...")
    async with Client(SERVER_URL) as client:
        tools = await client.list_tools()
        print(f"Discovered {len(tools)} tools: {[t.name for t in tools]}")
        for t in tools:
            print(f"  - {t.name}: {t.description.strip().splitlines()[0] if t.description else ''}")

        print()
        print("Calling ask_hr_policy(question='How many carry-over days are allowed in APAC?')...")
        result = await client.call_tool(
            "ask_hr_policy",
            {"question": "How many carry-over days are allowed in APAC?", "region": "APAC"},
        )
        print("Result:", result.content[0].text if result.content else result)

        print()
        print("Calling list_supported_regions()...")
        result = await client.call_tool("list_supported_regions", {})
        print("Result:", result.content[0].text if result.content else result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Could not connect -- is the server running? Start it first with:\n"
              f"  python mcp_server/hris_server.py --http --port 8765\n\nError: {e}", file=sys.stderr)
        sys.exit(1)
