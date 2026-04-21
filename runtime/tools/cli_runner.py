"""
cli_runner.py - smoke test interactivo con MCP tools
Uso: MODE=cli python -m runtime.entrypoint
"""
import asyncio
import json
import os
import anthropic

MODEL = os.getenv("ATLAS_MODEL", "claude-haiku-4-5-20251001")

SYSTEM = (
    "Eres Atlas, PM-Agent de Felirni Labs. "
    "Espanol neutro, tuteo estricto. "
    "Respuestas directas y accionables. "
    "Cuando uses una tool, muestra el resultado antes de analizar."
)

async def _get_tools_def():
    from runtime.mcp_server import list_tools
    mcp_tools = await list_tools()
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema if hasattr(t, "inputSchema") else {"type": "object", "properties": {}},
        }
        for t in mcp_tools
    ]

async def _call_mcp(name: str, inputs: dict) -> dict:
    from runtime.mcp_server import call_tool
    try:
        result = await call_tool(name, inputs)
        if hasattr(result, "content"):
            return {"result": [c.text if hasattr(c, "text") else str(c) for c in result.content]}
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}

async def run_cli():
    client = anthropic.Anthropic()
    tools = await _get_tools_def()
    history = []

    print(f"[Atlas CLI] modelo={MODEL} | tools={len(tools)} | Ctrl+C para salir\n")

    while True:
        try:
            user_input = input("Santi > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Atlas CLI] Sesion cerrada.")
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM,
            tools=tools,
            messages=history,
        )

        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await _call_mcp(block.name, block.input)
                    preview = json.dumps(result, ensure_ascii=False)[:120]
                    print(f"  [tool:{block.name}] {preview}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
            history.append({"role": "assistant", "content": response.content})
            history.append({"role": "user", "content": tool_results})
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM,
                tools=tools,
                messages=history,
            )

        final = "".join(b.text for b in response.content if hasattr(b, "text"))
        history.append({"role": "assistant", "content": final})
        print(f"\nAtlas > {final}\n")

def main():
    asyncio.run(run_cli())
