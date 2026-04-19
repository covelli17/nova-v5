# Atlas PM-Agent - Felirni Labs

PM-Agent operativo de Felirni Labs. Primer outcome real de Nova v5.

## Loop
`companies/felirni/context.md` + `outcomes/felirni/atlas/prompt.md` → agent run → log persistido en `logs/outcomes/felirni/atlas/`.

## Archivos
- `prompt.md` — rol, principios, formato de outputs, tono
- `config.py` — `ClaudeAgentOptions` con `setting_sources=[]`, Haiku default, MCP servers
- `run.py` — entry point CLI

## Cómo correr

Desde la raíz del repo:

```bash
python outcomes/felirni/atlas/run.py "status semanal del sprint"
python outcomes/felirni/atlas/run.py "triage correos" --input inputs/correos.md
```

## Context sourcing
El prompt final se compone en runtime:
1. `prompt.md` — rol y principios genéricos de Atlas
2. `companies/felirni/context.md` — estado actual de Felirni

Si cambia el sprint, el equipo o los proyectos, actualiza `companies/felirni/context.md`, **no este outcome**.

## Modelo
Default `claude-haiku-4-5`. Atlas escala a Sonnet/Opus vía tools (`invoke_sonnet`, `invoke_opus`) cuando razone que la tarea lo requiere.

## Deuda técnica
Los wrappers `@tool` viven inline en `config.py`. Cuando existan 2+ outcomes que reutilicen las mismas primitives/models, refactorizar a helpers en `tools/primitives/server.py` y `tools/models/server.py`.
