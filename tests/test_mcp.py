from app.agent.mcp_client import mcp_manager


def test_mcp_discovery():
    tools = mcp_manager.discover_tools()
    names = {tool["name"] for tool in tools}
    assert "get_order_tool" in names
    assert "cancel_order_tool" in names
    assert "refund_order_tool" in names


def test_mcp_tool_call():
    mcp_manager.discover_tools()
    result = mcp_manager.call_tool(
        "get_order_tool",
        {"order_id": "ORD001"},
    )
    assert result["success"] is True
