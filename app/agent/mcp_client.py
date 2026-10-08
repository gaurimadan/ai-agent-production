import asyncio
import json
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

    async def discover_tools_async(self):
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
                self.tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

                return self.tools

    def discover_tools(self):
        return asyncio.run(self.discover_tools_async())

    def get_cached_tools(self):
        return self.tools

    async def call_tool_async(self, tool_name: str, arguments: dict):
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

    @staticmethod
    def _normalize_tool_result(result):
        if getattr(result, "isError", False):
            return {
                "success": False,
                "error": "MCP tool call failed.",
            }

        structured_content = getattr(result, "structuredContent", None)
        if isinstance(structured_content, dict):
            return structured_content

        for item in getattr(result, "content", []):
            text = getattr(item, "text", None)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"success": True, "content": text}

        return {"success": True, "content": []}

    def call_tool(self, tool_name: str, arguments: dict):
        return self.call_tool_sync(tool_name, arguments)

    def call_tool_sync(self, tool_name: str, arguments: dict):
        """
        Safely execute the async MCP client from a synchronous
        LangGraph node.
        """

        def run():
            return asyncio.run(
                self.call_tool_async(
                    tool_name,
                    arguments,
                )
            )

        # Always execute the async MCP client in a separate thread.
        # This avoids event-loop conflicts.
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run)
            return self._normalize_tool_result(future.result())


mcp_manager = MCPManager()