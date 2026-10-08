import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agent.graph import GRAPH
from app.agent.mcp_client import mcp_manager
from app.observability import get_langfuse_callbacks


app = FastAPI(
    title="Production-Style MCP LangGraph Agent",
    version="1.0.0",
)


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool


@app.on_event("startup")
async def startup() -> None:
    await mcp_manager.discover_tools_async()


@app.get("/")
def root():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    return {
        "status": "running",
        "service": "production-style-agent",
    }


@app.get("/tools")
def tools():
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for tool in mcp_manager.get_cached_tools()
        ]
    }


@app.post("/webhook")
def webhook(request: AgentRequest):
    thread_id = request.thread_id or f"api-{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "callbacks": get_langfuse_callbacks(),
    }

    result = GRAPH.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request.message,
                }
            ],
            "user_query": request.message,
            "step_count": 0,
        },
        config=config,
    )

    if result.get("__interrupt__"):
        interrupt_value = result["__interrupt__"][0].value

        return {
            "status": "approval_required",
            "thread_id": thread_id,
            "approval": interrupt_value,
        }

    return {
        "status": "completed",
        "thread_id": thread_id,
        "response": result.get("final_response", ""),
    }


@app.post("/approve")
def approve(request: ApprovalRequest):
    config = {
        "configurable": {
            "thread_id": request.thread_id,
        },
        "callbacks": get_langfuse_callbacks(),
    }

    result = GRAPH.invoke(
        Command(
            resume={
                "approved": request.approved,
            }
        ),
        config=config,
    )

    if result.get("__interrupt__"):
        interrupt_value = result["__interrupt__"][0].value

        return {
            "status": "approval_required",
            "thread_id": request.thread_id,
            "approval": interrupt_value,
        }

    return {
        "status": "completed",
        "thread_id": request.thread_id,
        "response": result.get("final_response", ""),
    }