"""Gemini Flash (marines) — velocidad, reconocimiento rapido."""
from ._gemini_client import call

MODEL = "gemini-flash-latest"


def invoke_gemini_marines(
    prompt: str, system: str | None = None, max_tokens: int = 2048
) -> str:
    return call(MODEL, prompt, system, max_tokens)
