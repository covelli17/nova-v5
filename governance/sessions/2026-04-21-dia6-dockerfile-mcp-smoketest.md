# Día 6 — Dockerfile + MCP Server + Smoke Test

## Estado al cierre
- HEAD: ver git log --oneline -1
- Guardian Risk Score: 18/100 (sin cambios — no se tocó código de seguridad)
- Tests: 108 PASSED (sin regresiones)

## Entregables cerrados

### Bloque 1: Sync + verificación
- Mac Santiago sincronizado, HEAD 3eca40e
- 108 tests PASSED en 1.72s

### Bloque 2: Dockerfile + entrypoint dual-mode
- MODE=slack_listener → runtime.tools.slack_bot:main
- MODE=cli → runtime.tools.cli_runner:main (smoke test / dev)
- docker build nova-atlas:day6 OK

### Bloque 3: MCP server
- runtime/mcp_server.py: 8 tools expuestas al Agent SDK
- Importa wrappers existentes de felirni_api.py (no reinventa API)
- Tools: blocked, overdue, stale, sprint, team, tickets, decisions, epics

### Bloque 4: Smoke test
- Modelo: claude-haiku-4-5-20251001 (protocolo Día 2)
- 76in / 87out tokens
- Atlas respondió en español neutro con status correcto del board

## Incidente
- ANTHROPIC_API_KEY anterior revocada (sk-ant-api03-ZyW8duZ...)
- Nueva key creada: nova-atlas-prod en console.anthropic.com
- .envrc actualizado y re-aprobado con direnv allow

## Deuda técnica abierta (sin cambios del Día 5)
- M-3 felirni_api: client leak sin context manager
- M-3 slack_bot: ClaudeSDKClient nuevo por mensaje bajo carga
- B-2/B-3 secrets_manager: sin allowlist + tracebacks suprimidos

## Día 7 — prioridades
1. cli_runner.py (modo CLI completo para smoke test interactivo)
2. Secret felirni en AWS Secrets Manager (nova/atlas/felirni/config)
3. CloudFormation stack atlas-platform (ECS + Lambda + IAM)
4. Primer schedule EventBridge live
