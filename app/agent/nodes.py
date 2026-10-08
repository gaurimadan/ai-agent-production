import asyncio
import json
import os
import re
import uuid
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.types import interrupt

from app.agent.compaction import compact_if_needed
from app.agent.hooks import post_tool_hook, pre_tool_hook
from app.agent.mcp_client import mcp_manager
from app.agent.prompts import build_reasoning_prompt
from app.agent.state import AgentState

load_dotenv()


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
    temperature=0,
    max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "512")),
)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL,
    )

    if fenced:
        return json.loads(fenced.group(1))

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("LLM did not return a JSON object.")


def reasoning_node(state: AgentState) -> dict[str, Any]:
    tools = mcp_manager.get_cached_tools()
    system_prompt = build_reasoning_prompt(tools)

    messages = state.get("messages", [])

    llm_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ] + messages

    response = llm.invoke(llm_messages)
    raw = str(response.content)

    try:
        decision = _extract_json(raw)
    except Exception as exc:
        decision = {
            "type": "final",
            "content": (
                "I could not safely parse the model decision. "
                f"Error: {exc}"
            ),
        }

    new_messages = messages + [
        {
            "role": "assistant",
            "content": raw,
        }
    ]

    if decision.get("type") == "tool_call":
        return {
            "messages": new_messages,
            "tool_request": {
                "tool": decision.get("tool"),
                "arguments": decision.get("arguments", {}),
            },
            "final_response": "",
            "step_count": state.get("step_count", 0) + 1,
        }

    final_response = decision.get("content", raw)

    return {
        "messages": new_messages,
        "tool_request": {},
        "final_response": final_response,
        "step_count": state.get("step_count", 0) + 1,
    }


def pre_tool_node(state: AgentState) -> dict[str, Any]:
    request = state.get("tool_request", {})

    tool_name = request.get("tool", "")
    arguments = request.get("arguments", {})

    schemas = mcp_manager.get_cached_tools()

    validation = pre_tool_hook(
        tool_name,
        arguments,
        schemas,
    )

    if not validation["ok"]:
        error = {
            "success": False,
            "status": validation["status"],
            "error": validation["error"],
        }

        messages = state.get("messages", []) + [
            {
                "role": "user",
                "content": (
                    f"Tool validation result for "
                    f"{tool_name}: {json.dumps(error)}"
                ),
            }
        ]

        return {
            "messages": messages,
            "tool_result": error,
            "approval_required": False,
            "approval_status": "",
        }

    return {
        "approval_required": validation.get(
            "requires_approval",
            False,
        ),
        "approval_status": (
            "pending"
            if validation.get("requires_approval")
            else "not_required"
        ),
        "tool_result": {},
        "error": "",
    }


def approval_node(state: AgentState) -> dict[str, Any]:
    request = state.get("tool_request", {})

    decision = interrupt(
        {
            "type": "human_approval",
            "message": "A high-risk tool call requires approval.",
            "tool": request.get("tool"),
            "arguments": request.get("arguments", {}),
            "instruction": (
                "Resume with {'approved': true} "
                "or {'approved': false}."
            ),
        }
    )

    approved = (
        isinstance(decision, dict)
        and decision.get("approved") is True
    )

    if approved:
        return {
            "approval_required": False,
            "approval_status": "approved",
            "tool_result": {},
        }

    rejection = {
        "success": False,
        "status": 403,
        "error": (
            "Human approval was rejected. "
            "The high-risk action was not executed."
        ),
    }

    messages = state.get("messages", []) + [
        {
            "role": "user",
            "content": (
                f"Tool result for {request.get('tool')}: "
                f"{json.dumps(rejection)}"
            ),
        }
    ]

    return {
        "approval_required": False,
        "approval_status": "rejected",
        "tool_result": rejection,
        "messages": messages,
    }


def execute_tool_node(state: AgentState) -> dict[str, Any]:
    request = state.get("tool_request", {})

    tool_name = request.get("tool", "")
    arguments = request.get("arguments", {})

    try:
        raw_result = mcp_manager.call_tool_sync(
            tool_name,
            arguments,
        )

        # MCP CallToolResult is not necessarily a plain dict.
        # Convert it to a serializable representation.
        if hasattr(raw_result, "model_dump"):
            raw_result = raw_result.model_dump()

        result = post_tool_hook(
            tool_name,
            arguments,
            raw_result,
        )

    except Exception as exc:
        result = {
            "tool": tool_name,
            "arguments": arguments,
            "result": {
                "success": False,
                "error": str(exc),
            },
            "processed": True,
        }

    messages = state.get("messages", []) + [
        {
            "role": "user",
            "content": (
                f"Tool result from {tool_name}: "
                f"{json.dumps(result, default=str)}"
            ),
        }
    ]

    return {
        "messages": messages,
        "tool_result": result,
        "approval_status": "executed",
        "step_count": state.get("step_count", 0) + 1,
    }


def compaction_node(state: AgentState) -> dict[str, Any]:
    messages, summary = compact_if_needed(
        state.get("messages", []),
        llm,
    )

    return {
        "messages": messages,
        "summary": summary or state.get("summary", ""),
    }