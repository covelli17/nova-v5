"""Configuración del outcome Atlas PM-Agent para Felirni Labs.

Construye los MCP servers en runtime siguiendo el patrón del smoke test día 2
(tests/test_agent_smoke.py): envolver funciones puras de tools/ con @tool y
crear el server con create_sdk_mcp_server.
"""
import sys
from pathlib import Path

OUTCOME_DIR = Path(__file__).resolve().parent
ROOT = OUTCOME_DIR.parent.parent.parent  # atlas -> felirni -> outcomes -> Nova/
sys.path.insert(0, str(ROOT))

from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions

from tools.primitives import (
    read_file as _read_file,
    write_file as _write_file,
)
from tools.models import (
    invoke_sonnet as _invoke_sonnet,
    invoke_opus as _invoke_opus,
)

CONTEXT_FILE = ROOT / "companies" / "felirni" / "context.md"
PROMPT_FILE = OUTCOME_DIR / "prompt.md"

DEFAULT_MODEL = "claude-haiku-4-5"

PRIMITIVES_SERVER_NAME = "atlas-felirni-primitives"
MODELS_SERVER_NAME = "atlas-felirni-models"


def load_system_prompt() -> str:
    prompt_base = PROMPT_FILE.read_text(encoding="utf-8")
    context = CONTEXT_FILE.read_text(encoding="utf-8")
    return (
        f"{prompt_base}\n\n"
        f"# CONTEXTO OPERATIVO - FELIRNI LABS\n\n"
        f"{context}"
    )


@tool(
    "read_file",
    "Lee un archivo del filesystem y retorna su contenido como string.",
    {"path": str},
)
async def read_file_tool(args: dict):
    content = _read_file(args["path"])
    return {"content": [{"type": "text", "text": content}]}


@tool(
    "write_file",
    "Escribe contenido a un archivo. Crea el archivo si no existe.",
    {"path": str, "content": str},
)
async def write_file_tool(args: dict):
    _write_file(args["path"], args["content"])
    return {"content": [{"type": "text", "text": f"OK: {args['path']}"}]}


@tool(
    "invoke_sonnet",
    "Invoca Claude Sonnet para razonamiento intermedio cuando Haiku no alcance.",
    {"prompt": str},
)
async def invoke_sonnet_tool(args: dict):
    result = _invoke_sonnet(args["prompt"])
    return {"content": [{"type": "text", "text": result}]}


@tool(
    "invoke_opus",
    "Invoca Claude Opus para razonamiento profundo cuando Sonnet no alcance.",
    {"prompt": str},
)
async def invoke_opus_tool(args: dict):
    result = _invoke_opus(args["prompt"])
    return {"content": [{"type": "text", "text": result}]}


def build_options(model: str = DEFAULT_MODEL) -> ClaudeAgentOptions:
    primitives_server = create_sdk_mcp_server(
        name=PRIMITIVES_SERVER_NAME,
        version="0.1.0",
        tools=[read_file_tool, write_file_tool],
    )
    models_server = create_sdk_mcp_server(
        name=MODELS_SERVER_NAME,
        version="0.1.0",
        tools=[invoke_sonnet_tool, invoke_opus_tool],
    )

    return ClaudeAgentOptions(
        model=model,
        system_prompt=load_system_prompt(),
        setting_sources=[],
        mcp_servers={
            "primitives": primitives_server,
            "models": models_server,
        },
        allowed_tools=[
            f"mcp__{PRIMITIVES_SERVER_NAME}__read_file",
            f"mcp__{PRIMITIVES_SERVER_NAME}__write_file",
            f"mcp__{MODELS_SERVER_NAME}__invoke_sonnet",
            f"mcp__{MODELS_SERVER_NAME}__invoke_opus",
        ],
        permission_mode="bypassPermissions",
        max_turns=20,
    )
