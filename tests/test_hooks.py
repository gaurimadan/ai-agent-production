from app.agent.hooks import pre_tool_hook


def test_missing_required_argument_returns_400():
    schemas = [
        {
            "name": "get_order_tool",
            "inputSchema": {"type": "object", "required": ["order_id"]},
        }
    ]

    result = pre_tool_hook("get_order_tool", {}, schemas)

    assert result["ok"] is False
    assert result["status"] == 400


def test_refund_requires_approval():
    schemas = [
        {
            "name": "refund_order_tool",
            "inputSchema": {"type": "object", "required": ["order_id"]},
        }
    ]

    result = pre_tool_hook("refund_order_tool", {"order_id": "ORD001"}, schemas)

    assert result["ok"] is True
    assert result["requires_approval"] is True
