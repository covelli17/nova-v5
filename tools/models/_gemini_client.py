"""Cliente Gemini compartido — singleton lazy."""
import os
from google import genai
from google.genai import types

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY no seteada en el entorno")
        _client = genai.Client(api_key=key)
    return _client


def call(
    model: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int = 2048,
) -> str:
    client = get_client()
    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        system_instruction=system,
    )
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    return resp.text or ""
