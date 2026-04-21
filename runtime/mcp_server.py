"""
MCP Server — expone FelirniAPI tools al Agent SDK.
Importa los wrappers existentes de runtime/tools/felirni_api.py.
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from runtime.tools.felirni_api import FelirniAPI, FelirniAPIError
from runtime.tools.secrets_manager import get_secret

app = Server("felirni-mcp")

def _get_api() -> FelirniAPI:
    cfg = get_secret("felirni", keys=["api_url", "api_key"])
    return FelirniAPI(base_url=cfg["api_url"], token=cfg["api_key"])

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="felirni_get_blocked",    description="[Atlas] Tickets bloqueados",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_overdue",    description="[Atlas] Tickets vencidos",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_stale",      description="[Atlas] Tickets sin update >48h",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_sprint",     description="[Atlas] Sprint activo y métricas",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_team",       description="[Atlas] TCC por persona + resumen",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_list_tickets",   description="Lista tickets con filtros opcionales",
             inputSchema={"type": "object", "properties": {
                 "status":      {"type": "string"},
                 "epic_id":     {"type": "string"},
                 "sprint_id":   {"type": "string"},
                 "assignee_id": {"type": "string"},
             }}),
        Tool(name="felirni_list_decisions", description="[Atlas] Log de decisiones",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_list_epics",     description="Lista épicas activas",
             inputSchema={"type": "object", "properties": {}}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        async with _get_api() as api:
            dispatch = {
                "felirni_get_blocked":    api.get_blocked_tickets,
                "felirni_get_overdue":    api.get_overdue_tickets,
                "felirni_get_stale":      api.get_stale_tickets,
                "felirni_get_sprint":     api.get_active_sprint,
                "felirni_get_team":       api.get_team_metrics,
                "felirni_list_decisions": api.list_decisions,
                "felirni_list_epics":     api.list_epics,
            }
            if name == "felirni_list_tickets":
                result = await api.list_tickets(
                    status=arguments.get("status"),
                    epic_id=arguments.get("epic_id"),
                    sprint_id=arguments.get("sprint_id"),
                    assignee_id=arguments.get("assignee_id"),
                )
            elif name in dispatch:
                result = await dispatch[name]()
            else:
                result = {"error": f"Tool '{name}' no implementada"}
    except FelirniAPIError as e:
        result = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]

async def main():
    async with stdio_server() as streams:
        await app.run(*streams, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
