"""Claude Haiku 4.5 — tareas rapidas, bajo costo."""
from ._anthropic_client import call

MODEL = "claude-haiku-4-5-20251001"


def invoke_haiku(prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
    return call(MODEL, prompt, system, max_tokens)
