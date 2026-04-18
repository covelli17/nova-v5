"""Gemini Flash-Lite (logistics) — volumen, costo minimo."""
from ._gemini_client import call

MODEL = "gemini-flash-lite-latest"


def invoke_gemini_logistics(
    prompt: str, system: str | None = None, max_tokens: int = 2048
) -> str:
    return call(MODEL, prompt, system, max_tokens)
