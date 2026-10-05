import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.agent.graph import GRAPH
from app.agent.mcp_client import mcp_manager
from app.observability import get_langfuse_callbacks

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "data" / "evaluation_cases.json"
OUTPUT_PATH = ROOT / "data" / "evaluation_results.json"

JUDGE_PROMPT = """
You are evaluating an AI agent's error recovery.

Score only error recovery from 1 to 5:
1 = fails to recover
2 = recognizes an error but does not recover correctly
3 = partial recovery
4 = correct recovery with minor issues
5 = detects the error, corrects the action, and reaches the correct result

Return JSON only:
{"score": 1, "reason": "..."}
"""


def judge(llm: ChatGroq, case: dict, trace: dict) -> dict:
    response = llm.invoke([
        {"role": "system", "content": JUDGE_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "input": case["input"],
                    "expected": case["expected"],
                    "trace": trace,
                },
                indent=2,
                default=str,
            ),
        },
    ])
    text = str(response.content).strip()
    start = text.find("{")
    end = text.rfind("}")
    return json.loads(text[start : end + 1])


def main() -> None:
    mcp_manager.discover_tools()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
    )

    results = []
    for index, case in enumerate(cases, start=1):
        thread_id = f"eval-{index}"
        config = {"configurable": {"thread_id": thread_id}, "callbacks": get_langfuse_callbacks()}
        state = GRAPH.invoke(
            {
                "messages": [{"role": "user", "content": case["input"]}],
                "user_query": case["input"],
                "step_count": 0,
            },
            config=config,
        )

        # For evaluation, an approval-required case is recorded as an interrupted trace.
        trace = {
            "final_response": state.get("final_response", ""),
            "messages": state.get("messages", []),
            "interrupted": bool(state.get("__interrupt__")),
        }
        grade = judge(llm, case, trace)
        results.append({"case": index, **grade, "trace": trace})
        print(f"Case {index}: {grade}")

    average = sum(item["score"] for item in results) / len(results)
    output = {"average_error_recovery_score": average, "results": results}
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\nAverage Error Recovery: {average:.2f}/5")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
