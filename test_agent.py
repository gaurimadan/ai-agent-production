from app.agent.graph import GRAPH
from app.agent.mcp_client import mcp_manager


if __name__ == "__main__":
    mcp_manager.discover_tools()

    result = GRAPH.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the status of ORD001?",
                }
            ],
            "user_query": "What is the status of ORD001?",
            "step_count": 0,
        },
        config={"configurable": {"thread_id": "smoke-test"}},
    )

    print(result.get("final_response", result))
