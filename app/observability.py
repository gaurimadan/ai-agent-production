import os

from dotenv import load_dotenv

load_dotenv()


def get_langfuse_callbacks():
    """Return Langfuse callbacks when credentials are configured.

    The agent still runs without Langfuse so Tasks 1-7 can be developed first.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        return []

    from langfuse import get_client
    from langfuse.langchain import CallbackHandler

    client = get_client()
    if not client.auth_check():
        print("Warning: Langfuse authentication failed; continuing without tracing.")
        return []

    return [CallbackHandler()]
