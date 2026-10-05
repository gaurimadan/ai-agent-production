import asyncio
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_FILE = PROJECT_ROOT / "app" / "mcp_server" / "server.py"


class MCPManager:
    def __init__(self):
        self.tools = []

    async def discover_tools(self):
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_FILE)],
            env={
                **os.environ,
                "PYTHONPATH": str(PROJECT_ROOT),
            },
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                response = await session.list_tools()
                self.tools = response.tools

                return self.tools

    def get_cached_tools(self):
        return self.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_FILE)],
            env={
                **os.environ,
                "PYTHONPATH": str(PROJECT_ROOT),
            },
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    tool_name,
                    arguments,
                )

                return result

    def call_tool_sync(self, tool_name: str, arguments: dict):
        """
        Safely execute the async MCP client from a synchronous
        LangGraph node.
        """

        def run():
            return asyncio.run(
                self.call_tool(
                    tool_name,
                    arguments,
                )
            )

        # Always execute the async MCP client in a separate thread.
        # This avoids event-loop conflicts.
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run)
            return future.result()


mcp_manager = MCPManager()