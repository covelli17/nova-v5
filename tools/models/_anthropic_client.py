"""Cliente Anthropic compartido — singleton lazy."""
import os
from anthropic import Anthropic

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY no seteada en el entorno")
        _client = Anthropic(api_key=key)
    return _client


def call(
    model: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int = 2048,
) -> str:
    client = get_client()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if b.type == "text")
