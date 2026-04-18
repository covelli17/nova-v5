# Sesion 2026-04-18 — Dia 2 Bloque 2: Tools primitives + models wrappers

## Objetivo
Construir el layer de herramientas del Agent Army: primitivas de filesystem/bash
y wrappers de modelos (Anthropic + Gemini). Validar con smoke test desde
Claude Agent SDK.

## Entregables
- `tools/primitives/`: read_file, write_file, run_bash (con allowlist + timeout)
- `tools/models/`: invoke_opus, invoke_sonnet, invoke_haiku,
  invoke_gemini_marines, invoke_gemini_logistics
- `tools/models/_anthropic_client.py` y `_gemini_client.py`: clientes singleton
- `tests/test_agent_smoke.py`: agent SDK invocando read_file como MCP tool

## Modelos mapeados
- Opus 4.7 → razonamiento profundo, decisiones criticas
- Sonnet 4.6 → workhorse balanceado
- Haiku 4.5 → tareas rapidas, bajo costo
- Gemini Flash (marines) → velocidad, reconocimiento rapido
- Gemini Flash-Lite (logistics) → volumen, costo minimo

## Validaciones
- Primitives smoke: write + read + run_bash → OK
- Haiku wrapper → OK
- Gemini Flash-Lite wrapper → OK
- Agent SDK end-to-end (Sonnet orquestando read_file via MCP) → OK
  - 6.7s, 8241 input tokens, 250 output tokens, $0.059
  - Tool call correcto, tool_result correcto, end_turn limpio

## Deuda tecnica registrada
1. Agent SDK hereda MCP servers de Claude Code local (Gmail, Calendar, etc).
   Aislar con `setting_sources=[]` en cada ClaudeAgentOptions de outcomes.
2. Smoke tests corriendo en Sonnet por default ($0.06/call). Forzar Haiku
   en tests no criticos para bajar costo ~20x.
3. Warning `GOOGLE_API_KEY` + `GEMINI_API_KEY` ambas seteadas. Limpiar
   `.envrc` dejando solo `GEMINI_API_KEY`.

## Decisiones
- Convencion de naming militar para Gemini: marines (Flash, alta velocidad),
  logistics (Flash-Lite, alto volumen).
- Clientes de modelos como singletons lazy via `get_client()` — un cliente
  por vendor reutilizado en todos los wrappers.
- Allowlist estricta en run_bash: solo comandos de inspeccion + toolchain
  Python/Git. Expandir solo cuando un outcome lo necesite y quede
  documentado.

## Proximo bloque
Dia 3: construir el primer outcome real (candidato: Atlas PM-Agent de Felirni
Labs) usando los primitives + models, validando el loop completo:
context.md por compania → outcome prompt → agent run → resultado persistido.
