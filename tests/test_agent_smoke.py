"""Smoke test Bloque 2 — Agent SDK invocando 1 primitive (read_file)."""
import sys
from pathlib import Path

# Agregar raiz del proyecto al sys.path para importar tools/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anyio
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeAgentOptions,
    ClaudeSDKClient,
)

from tools.primitives import read_file as _read_file


@tool(
    "read_file",
    "Lee un archivo del filesystem y retorna su contenido como string.",
    {"path": str},
)
async def read_file_tool(args: dict):
    content = _read_file(args["path"])
    return {"content": [{"type": "text", "text": content}]}


async def main():
    server = create_sdk_mcp_server(
        name="nova-primitives",
        version="0.1.0",
        tools=[read_file_tool],
    )

    options = ClaudeAgentOptions(
        mcp_servers={"nova": server},
        allowed_tools=["mcp__nova-primitives__read_file"],
        permission_mode="bypassPermissions",
        system_prompt=(
            "Eres un agente de smoke test de Nova v5. "
            "Usa las herramientas disponibles para responder. Se directo y breve."
        ),
    )

    prompt = (
        "Lee el archivo /tmp/nova_test.txt usando read_file y "
        "dime exactamente su contenido en una sola palabra."
    )

    print("=" * 60)
    print("NOVA v5 — Smoke Test Agent SDK")
    print("=" * 60)

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for msg in client.receive_response():
            print(msg)

    print("=" * 60)
    print("Smoke test completado.")


if __name__ == "__main__":
    anyio.run(main)
