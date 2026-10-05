import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    approval_node,
    compaction_node,
    execute_tool_node,
    pre_tool_node,
    reasoning_node,
)
from app.agent.state import AgentState


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "checkpoints.sqlite"


def route_reasoning(state: AgentState) -> str:
    return "tool" if state.get("tool_request") else "final"


def route_pre_tool(state: AgentState) -> str:
    if state.get("tool_result", {}).get("status") == 400:
        return "error"
    return "approval" if state.get("approval_required") else "execute"


def route_approval(state: AgentState) -> str:
    if state.get("approval_status") == "approved":
        return "execute"
    return "rejected"


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("reasoning", reasoning_node)
    builder.add_node("pre_tool", pre_tool_node)
    builder.add_node("approval", approval_node)
    builder.add_node("execute_tool", execute_tool_node)
    builder.add_node("compact", compaction_node)

    builder.add_edge(START, "reasoning")

    builder.add_conditional_edges(
        "reasoning",
        route_reasoning,
        {
            "tool": "pre_tool",
            "final": END,
        },
    )

    builder.add_conditional_edges(
        "pre_tool",
        route_pre_tool,
        {
            "error": "reasoning",
            "approval": "approval",
            "execute": "execute_tool",
        },
    )

    builder.add_conditional_edges(
        "approval",
        route_approval,
        {
            "execute": "execute_tool",
            "rejected": "reasoning",
        },
    )

    builder.add_edge("execute_tool", "compact")
    builder.add_edge("compact", "reasoning")

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    return builder.compile(checkpointer=checkpointer)


GRAPH = build_graph()
