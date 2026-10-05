from typing import Any

from langchain_groq import ChatGroq

from app.agent.prompts import SUMMARY_PROMPT



def compact_if_needed(
    messages: list[dict[str, Any]],
    llm: ChatGroq,
) -> tuple[list[dict[str, Any]], str | None]:
    """If the history exceeds 10 messages, summarize the first 8."""
    if len(messages) <= 10:
        return messages, None

    first_eight = messages[:8]
    remaining = messages[8:]
    transcript = "\n".join(
        f"{message.get('role', 'unknown')}: {message.get('content', '')}"
        for message in first_eight
    )

    response = llm.invoke([
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": transcript},
    ])
    summary = str(response.content)

    compacted = [
        {
            "role": "system",
            "content": f"Conversation summary of earlier messages: {summary}",
        }
    ] + remaining

    return compacted, summary
