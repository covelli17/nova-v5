# Día 5 — felirni_api.py + slack_bot.py

## Estado al cierre
- HEAD: ver git log --oneline -1
- Guardian Risk Score proyecto: 18/100 (Bajo)

## Entregables cerrados

### Block 1: felirni_api.py
- 32 endpoints mapeados desde docstring del handler (tickets 9, epics 7, sprints 7, people 5, metrics 1, decisions 3)
- 46 tests PASSED (29 funcionales + 17 seguridad)
- Guardian: 38 → 30 → 18/100
- Hallazgos cerrados: A-1 SSRF (link-local/16 + RFC1918 + loopback), M-1 path injection, M-2 token leak

### Block 2: slack_bot.py
- Dual mode: socket (dev) + http (Lambda/EventBridge)
- 25 tests PASSED
- Guardian: 62 → 18/100
- Hallazgos cerrados: C-1 firma Slack HMAC, A-1 prompt injection, A-2 token leak en logs

## Decisiones cerradas
- D3: cluster nuevo nova-atlas-cluster (ECS)
- D4: canal #nova-atlas-sandbox para smoke test

## Deuda técnica abierta (Bajos — no bloquean producción)
- M-3 felirni_api: client leak sin context manager (riesgo disponibilidad)
- M-3 slack_bot: ClaudeSDKClient nuevo por mensaje bajo carga
- B-3 slack_bot: _resolve_self_identity falla silenciosamente
- B-2 secrets_manager: sin allowlist de compañías
- B-3 secrets_manager: tracebacks suprimidos sin logger

## Día 6 — prioridades
1. Dockerfile + entrypoint dual-mode (SLACK_LISTENER vs EVENTBRIDGE)
2. Smoke test end-to-end en #nova-atlas-sandbox
3. Conectar FelirniAPI tools al Agent SDK via MCP
