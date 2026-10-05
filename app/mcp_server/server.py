import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from app.tools.orders_tools import (
    get_order,
    cancel_order,
    refund_order,
)


mcp = FastMCP("Order Management MCP Server")


@mcp.tool()
def get_order_tool(order_id: str) -> dict:
    """Get information about an order."""
    return get_order(order_id)


@mcp.tool()
def cancel_order_tool(order_id: str) -> dict:
    """Cancel a shipped order."""
    return cancel_order(order_id)


@mcp.tool()
def refund_order_tool(order_id: str) -> dict:
    """Initiate a refund for an order."""
    return refund_order(order_id)


if __name__ == "__main__":
    mcp.run()