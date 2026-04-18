"""Claude Opus 4.7 — razonamiento profundo, decisiones criticas."""
from ._anthropic_client import call

MODEL = "claude-opus-4-7"


def invoke_opus(prompt: str, system: str | None = None, max_tokens: int = 2048) -> str:
    return call(MODEL, prompt, system, max_tokens)
