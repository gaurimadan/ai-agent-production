from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    messages: list[dict[str, Any]]
    user_query: str
    tool_request: dict[str, Any]
    tool_result: dict[str, Any]
    final_response: str
    approval_required: bool
    approval_status: str
    error: str
    summary: str
    step_count: int
