"""
MCP Server — expone FelirniAPI tools al Agent SDK.
Día 11: Autonomía completa - 31 tools (READ + WRITE).
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from runtime.tools.felirni_api import FelirniAPI, FelirniAPIError
from runtime.tools.secrets_manager import get_felirni_config

app = Server("felirni-mcp")

def _get_api() -> FelirniAPI:
    cfg = get_felirni_config()
    return FelirniAPI(base_url=cfg["api_url"], token=cfg["api_key"])

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # READ: Tickets
        Tool(name="felirni_get_blocked",    description="[Atlas] Tickets bloqueados",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_overdue",    description="[Atlas] Tickets vencidos",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_stale",      description="[Atlas] Tickets sin update >48h",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_list_tickets",   description="Lista tickets con filtros opcionales",
             inputSchema={"type": "object", "properties": {
                 "status":      {"type": "string"},
                 "epic_id":     {"type": "string"},
                 "sprint_id":   {"type": "string"},
                 "assignee_id": {"type": "string"},
             }}),
        Tool(name="felirni_get_ticket",     description="Obtiene detalles de un ticket específico",
             inputSchema={"type": "object", "properties": {
                 "ticket_id": {"type": "string", "description": "ID del ticket"}
             }, "required": ["ticket_id"]}),

        # WRITE: Tickets
        Tool(name="felirni_create_ticket",  description="Crea un nuevo ticket",
             inputSchema={"type": "object", "properties": {
                 "body": {"type": "object", "description": "Datos del ticket (title, description, status, assignee, etc.)"}
             }, "required": ["body"]}),
        Tool(name="felirni_update_ticket",  description="Actualiza un ticket existente",
             inputSchema={"type": "object", "properties": {
                 "ticket_id": {"type": "string"},
                 "body": {"type": "object", "description": "Campos a actualizar"}
             }, "required": ["ticket_id", "body"]}),
        Tool(name="felirni_delete_ticket",  description="Elimina un ticket",
             inputSchema={"type": "object", "properties": {
                 "ticket_id": {"type": "string"}
             }, "required": ["ticket_id"]}),
        Tool(name="felirni_add_comment",    description="Agrega comentario a un ticket",
             inputSchema={"type": "object", "properties": {
                 "ticket_id": {"type": "string"},
                 "body": {"type": "object", "description": "Comentario con author y text"}
             }, "required": ["ticket_id", "body"]}),

        # READ: Sprints
        Tool(name="felirni_get_sprint",     description="[Atlas] Sprint activo y métricas",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_list_sprints",   description="Lista todos los sprints",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_sprint_metrics", description="Métricas de un sprint específico",
             inputSchema={"type": "object", "properties": {
                 "sprint_id": {"type": "string"}
             }, "required": ["sprint_id"]}),

        # WRITE: Sprints
        Tool(name="felirni_create_sprint",  description="Crea un nuevo sprint",
             inputSchema={"type": "object", "properties": {
                 "body": {"type": "object", "description": "Datos del sprint (name, startDate, endDate, etc.)"}
             }, "required": ["body"]}),
        Tool(name="felirni_update_sprint",  description="Actualiza un sprint",
             inputSchema={"type": "object", "properties": {
                 "sprint_id": {"type": "string"},
                 "body": {"type": "object"}
             }, "required": ["sprint_id", "body"]}),
        Tool(name="felirni_close_sprint",   description="Cierra un sprint con reporte",
             inputSchema={"type": "object", "properties": {
                 "sprint_id": {"type": "string"},
                 "body": {"type": "object", "description": "Datos de cierre (opcional)"}
             }, "required": ["sprint_id"]}),
        Tool(name="felirni_delete_sprint",  description="Elimina un sprint",
             inputSchema={"type": "object", "properties": {
                 "sprint_id": {"type": "string"}
             }, "required": ["sprint_id"]}),

        # READ: Épicas
        Tool(name="felirni_list_epics",     description="Lista épicas activas",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_epic_tasks",  description="Obtiene tasks de una épica",
             inputSchema={"type": "object", "properties": {
                 "epic_id": {"type": "string"}
             }, "required": ["epic_id"]}),
        Tool(name="felirni_get_epic_progress", description="Obtiene progreso de una épica",
             inputSchema={"type": "object", "properties": {
                 "epic_id": {"type": "string"}
             }, "required": ["epic_id"]}),
        Tool(name="felirni_get_at_risk_epics", description="Épicas en riesgo",
             inputSchema={"type": "object", "properties": {}}),

        # WRITE: Épicas
        Tool(name="felirni_create_epic",    description="Crea una nueva épica",
             inputSchema={"type": "object", "properties": {
                 "body": {"type": "object", "description": "Datos de la épica (title, description, etc.)"}
             }, "required": ["body"]}),
        Tool(name="felirni_update_epic",    description="Actualiza una épica",
             inputSchema={"type": "object", "properties": {
                 "epic_id": {"type": "string"},
                 "body": {"type": "object"}
             }, "required": ["epic_id", "body"]}),
        Tool(name="felirni_delete_epic",    description="Elimina una épica",
             inputSchema={"type": "object", "properties": {
                 "epic_id": {"type": "string"}
             }, "required": ["epic_id"]}),

        # READ: People
        Tool(name="felirni_get_team",       description="[Atlas] TCC por persona + resumen",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_list_people",    description="Lista todas las personas del equipo",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="felirni_get_person_tasks", description="Obtiene tasks de una persona",
             inputSchema={"type": "object", "properties": {
                 "person_id": {"type": "string"}
             }, "required": ["person_id"]}),
        Tool(name="felirni_get_person_tcc", description="Obtiene TCC score de una persona",
             inputSchema={"type": "object", "properties": {
                 "person_id": {"type": "string"}
             }, "required": ["person_id"]}),

        # WRITE: People
        Tool(name="felirni_create_person",  description="Crea una nueva persona en el equipo",
             inputSchema={"type": "object", "properties": {
                 "body": {"type": "object", "description": "Datos de la persona (name, role, email, etc.)"}
             }, "required": ["body"]}),
        Tool(name="felirni_update_person",  description="Actualiza datos de una persona",
             inputSchema={"type": "object", "properties": {
                 "person_id": {"type": "string"},
                 "body": {"type": "object"}
             }, "required": ["person_id", "body"]}),

        # READ: Decisions
        Tool(name="felirni_list_decisions", description="[Atlas] Log de decisiones",
             inputSchema={"type": "object", "properties": {}}),

        # WRITE: Decisions
        Tool(name="felirni_create_decision", description="Registra una nueva decisión",
             inputSchema={"type": "object", "properties": {
                 "body": {"type": "object", "description": "Datos de la decisión (title, context, decision, etc.)"}
             }, "required": ["body"]}),
        Tool(name="felirni_update_decision", description="Actualiza una decisión",
             inputSchema={"type": "object", "properties": {
                 "decision_id": {"type": "string"},
                 "body": {"type": "object"}
             }, "required": ["decision_id", "body"]}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        async with _get_api() as api:
            # READ: Tickets
            if name == "felirni_get_blocked":
                result = await api.get_blocked_tickets()
            elif name == "felirni_get_overdue":
                result = await api.get_overdue_tickets()
            elif name == "felirni_get_stale":
                result = await api.get_stale_tickets()
            elif name == "felirni_list_tickets":
                result = await api.list_tickets(
                    status=arguments.get("status"),
                    epic_id=arguments.get("epic_id"),
                    sprint_id=arguments.get("sprint_id"),
                    assignee_id=arguments.get("assignee_id"),
                )
            elif name == "felirni_get_ticket":
                result = await api.get_ticket(arguments["ticket_id"])

            # WRITE: Tickets
            elif name == "felirni_create_ticket":
                result = await api.create_ticket(arguments["body"])
            elif name == "felirni_update_ticket":
                result = await api.update_ticket(arguments["ticket_id"], arguments["body"])
            elif name == "felirni_delete_ticket":
                result = await api.delete_ticket(arguments["ticket_id"])
            elif name == "felirni_add_comment":
                result = await api.add_comment(arguments["ticket_id"], arguments["body"])

            # READ: Sprints
            elif name == "felirni_get_sprint":
                result = await api.get_active_sprint()
            elif name == "felirni_list_sprints":
                result = await api.list_sprints()
            elif name == "felirni_get_sprint_metrics":
                result = await api.get_sprint_metrics(arguments["sprint_id"])

            # WRITE: Sprints
            elif name == "felirni_create_sprint":
                result = await api.create_sprint(arguments["body"])
            elif name == "felirni_update_sprint":
                result = await api.update_sprint(arguments["sprint_id"], arguments["body"])
            elif name == "felirni_close_sprint":
                result = await api.close_sprint(arguments["sprint_id"], arguments.get("body"))
            elif name == "felirni_delete_sprint":
                result = await api.delete_sprint(arguments["sprint_id"])

            # READ: Épicas
            elif name == "felirni_list_epics":
                result = await api.list_epics()
            elif name == "felirni_get_epic_tasks":
                result = await api.get_epic_tasks(arguments["epic_id"])
            elif name == "felirni_get_epic_progress":
                result = await api.get_epic_progress(arguments["epic_id"])
            elif name == "felirni_get_at_risk_epics":
                result = await api.get_at_risk_epics()

            # WRITE: Épicas
            elif name == "felirni_create_epic":
                result = await api.create_epic(arguments["body"])
            elif name == "felirni_update_epic":
                result = await api.update_epic(arguments["epic_id"], arguments["body"])
            elif name == "felirni_delete_epic":
                result = await api.delete_epic(arguments["epic_id"])

            # READ: People
            elif name == "felirni_get_team":
                result = await api.get_team_metrics()
            elif name == "felirni_list_people":
                result = await api.list_people()
            elif name == "felirni_get_person_tasks":
                result = await api.get_person_tasks(arguments["person_id"])
            elif name == "felirni_get_person_tcc":
                result = await api.get_person_tcc(arguments["person_id"])

            # WRITE: People
            elif name == "felirni_create_person":
                result = await api.create_person(arguments["body"])
            elif name == "felirni_update_person":
                result = await api.update_person(arguments["person_id"], arguments["body"])

            # READ: Decisions
            elif name == "felirni_list_decisions":
                result = await api.list_decisions()

            # WRITE: Decisions
            elif name == "felirni_create_decision":
                result = await api.create_decision(arguments["body"])
            elif name == "felirni_update_decision":
                result = await api.update_decision(arguments["decision_id"], arguments["body"])

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
