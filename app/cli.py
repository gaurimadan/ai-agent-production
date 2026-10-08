import asyncio

from langgraph.types import Command

from app.agent.graph import GRAPH
from app.agent.mcp_client import mcp_manager


def run():
    asyncio.run(mcp_manager.discover_tools_async())

    thread_id = "cli-session"

    print("Production AI Agent CLI")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            break

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        result = GRAPH.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                "user_query": user_input,
                "step_count": 0,
            },
            config=config,
        )

        if result.get("__interrupt__"):
            interrupt_data = result["__interrupt__"][0].value

            print("\n⚠️ HUMAN APPROVAL REQUIRED")
            print(f"Tool: {interrupt_data.get('tool')}")
            print(f"Arguments: {interrupt_data.get('arguments')}")
            print(f"Message: {interrupt_data.get('message')}")

            while True:
                choice = input("\nApprove or Reject? [a/r]: ").strip().lower()

                if choice in ("a", "approve"):
                    approved = True
                    break

                if choice in ("r", "reject"):
                    approved = False
                    break

                print("Please enter 'a' for approve or 'r' for reject.")

            result = GRAPH.invoke(
                Command(
                    resume={
                        "approved": approved
                    }
                ),
                config=config,
            )

        print("\nAgent:", result.get("final_response", ""))
        print()


if __name__ == "__main__":
    run()