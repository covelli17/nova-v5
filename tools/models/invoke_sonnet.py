"""Claude Sonnet 4.6 — workhorse balanceado."""
from ._anthropic_client import call

MODEL = "claude-sonnet-4-6"


def invoke_sonnet(prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
    return call(MODEL, prompt, system, max_tokens)
