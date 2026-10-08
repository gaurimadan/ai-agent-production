from typing import Any


HIGH_RISK_TOOLS = {"refund_order_tool"}


def pre_tool_hook(
    tool_name: str,
    arguments: dict[str, Any],
    tool_schemas: list[Any],
) -> dict[str, Any]:
    """Deterministic validation before an LLM-selected MCP call."""

    schema_by_name = {
        (tool.get("name") if isinstance(tool, dict) else tool.name): tool
        for tool in tool_schemas
    }

    if tool_name not in schema_by_name:
        return {
            "ok": False,
            "status": 400,
            "error": (
                f"Unknown tool '{tool_name}'. "
                f"Available tools: {sorted(schema_by_name)}"
            ),
        }

    if not isinstance(arguments, dict):
        return {
            "ok": False,
            "status": 400,
            "error": "Tool arguments must be a JSON object.",
        }

    tool = schema_by_name[tool_name]

    input_schema = (
        tool.get("inputSchema", {})
        if isinstance(tool, dict)
        else getattr(tool, "inputSchema", {})
    ) or {}

    required = input_schema.get("required", [])

    missing = [
        key
        for key in required
        if key not in arguments
    ]

    if missing:
        return {
            "ok": False,
            "status": 400,
            "error": (
                f"Missing required argument(s): "
                f"{', '.join(missing)}"
            ),
        }

    return {
        "ok": True,
        "requires_approval": tool_name in HIGH_RISK_TOOLS,
    }


def post_tool_hook(
    tool_name: str,
    arguments: dict[str, Any],
    result: Any,
) -> dict[str, Any]:
    """Normalize the tool result before it is returned."""

    return {
        "tool": tool_name,
        "arguments": arguments,
        "result": result,
        "processed": True,
    }