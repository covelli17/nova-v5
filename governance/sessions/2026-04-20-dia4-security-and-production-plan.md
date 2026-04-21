# Dia 4 — Seguridad de primitives + plan de produccion multi-compania

**Fecha:** 2026-04-20
**Mac:** Santiago
**Duracion:** ~5h netas (con sync inicial + pausa entre bloques)

## Objetivo del dia

1. Cerrar deudas altas de seguridad del dia 3 (Guardian NG-001 y NG-003)
2. Declarar dependencias del proyecto
3. Disenar arquitectura de produccion multi-compania para Atlas

## Entregables

### Seguridad (AM-PM primera mitad)
- `tools/primitives/_safety.py` con `assert_path_in_allowed_root()` — path confinement con resolve+is_relative_to, simetrico en ambos lados para anular symlink escape
- `tools/primitives/read_file.py` y `write_file.py` llaman al helper como primera operacion
- `tools/primitives/run_bash.py` refactor: `shell=False`, tokens como lista a subprocess, FORBIDDEN_CHARS explicitos
- `tests/test_primitives_safety.py` (6 tests) y `tests/test_run_bash_safety.py` (12 tests), todos pass
- `requirements.txt` con 4 runtime deps pinneadas, `requirements-dev.txt` con pytest
- `.gitignore` expandido: logs/, nova-guardian/*, .pcloudignore, .venv symlink, caches Python
- `governance/security/2026-04-19-guardian-report.md` archivado

### Produccion (PM segunda mitad)
- Auditoria forense de infra viva: AWS autenticado como m1-deploy-user, Felirni con Lambda/DynamoDB/API Gateway operativos, 145 items reales en felirni-db-prod, frontend HTTP 200
- Rename `GUIA-FELIPE.md` -> `~/Proyectos/M1/docs/GUIA-DEPLOY-BOARD-SC17.md` (aplicable a todo el portfolio, no solo Felipe)
- `governance/architecture/atlas-multi-company-production.md` — arquitectura ECS Fargate + EventBridge + Lambda, ~13 USD/mes para 7 companias, con roadmap dia 5-12

## Resultado Guardian

| Dimension | Inicio dia | Fin dia |
|---|---|---|
| Risk Score | 62/100 | 28/100 |
| Altos abiertos | 3 | 0 |
| Tests | 0 | 19 pass |
| Dependencias declaradas | No | Si |

3 capas de defensa activas: path confinement, shell=False, FORBIDDEN_CHARS.

## Hallazgos clave del reconocimiento

1. **Infra Felirni en AWS ya operativa** con 145 items DynamoDB, API health responde `"atlas": true` (version 3.0.0)
2. **API URL:** `https://le0dj70e7i.execute-api.us-east-1.amazonaws.com/prod`
3. **Lambda:** felirni-project-api-prod, DynamoDB: felirni-db-prod
4. **Codigo fuente de la Lambda no esta en Mac Santiago** — probablemente en Mac Lulo o repo separado
5. **Slack bot token no esta en Keychain ni env vars en Mac Santiago** — hay que regenerar o ubicar
6. **Secrets Manager vacio** — decidido usar Secrets Manager como home de secrets de produccion
7. **CloudFormation stack de Felirni no aparece con filtros estandar** — infra probablemente deployada fuera de IaC, investigar dia 5

## Decisiones tomadas

- **DEC-04-001:** Adoptar ECS Fargate + EventBridge + Lambda como plataforma de Atlas. Rechazadas: Railway (2a plataforma), solo Lambda (no WebSocket), Mac launchd (no escala), solo Fargate (overhead schedules)
- **DEC-04-002:** CloudFormation YAML para IaC, consistente con Lambdas M1/Felirni existentes. Rechazados: Terraform (nuevo toolchain), CDK (framework nuevo sin beneficio claro)
- **DEC-04-003:** Secrets Manager como home unico de secretos de produccion. Rechazado: Keychain macOS (no accesible desde Fargate/Lambda)
- **DEC-04-004:** Rename `GUIA-FELIPE.md` a `GUIA-DEPLOY-BOARD-SC17.md` — aplicable a todo el portfolio
- **DEC-04-005:** Reportes de Guardian archivados en `governance/security/` pero el skill Nova Guardian NO entra al repo (vive en ~/Documents/Nova/ como skill global de Claude Code)

## Deudas tecnicas abiertas

### Prioridad alta dia 5
1. Recuperar codigo fuente de Lambda Felirni (sync desde Mac Lulo o repo separado)
2. Decidir Slack App strategy: uno por compania vs multi-workspace (D1 del architecture doc)
3. Ubicar o regenerar Slack Bot Token y API key de felirni-frontend-key-prod (via AWS CLI para la key)
4. Tool wrappers: `platform/tools/felirni_api.py`, `slack_bot.py`, `secrets_manager.py` con tests

### Prioridad media dia 6-7
5. Guardian NG-004 (prompt injection en run.py) — envolver `input_payload` con delimitadores
6. Guardian NG-005 (budget cap en ClaudeAgentOptions)
7. Dockerfile + entrypoint.py dual-mode (listener/scheduled)
8. CloudFormation template `infrastructure/atlas-platform.yaml`

### Backlog dia 8+
9. Refactor `@tool` wrappers a helpers reutilizables cuando existan 2+ outcomes
10. Introducir `outcomes/_base/atlas/prompt.md` con inheritance via overlays — dia 10 cuando tengamos 3+ outcomes y veamos drift real

## Proxima sesion

**Dia 5 — prioridad:** tool wrappers. Arranca con `platform/tools/secrets_manager.py` (es el bloque base de los otros dos), despues `felirni_api.py`, despues `slack_bot.py`. Cada uno con tests. Guardian check al final. Decidir D1 (Slack App strategy) antes de que secrets_manager.py defina la estructura del secret.

Antes de arrancar dia 5 leer:
- Este archivo
- `governance/architecture/atlas-multi-company-production.md`

## Hallazgo tardio — carpeta ia-board-server en Documents/AWS

Santi detecto al cierre del dia la carpeta `~/Documents/AWS/ia-board-server/` con:
- Backend Node.js (server.js, package.json)
- db.json como storage (NO DynamoDB)
- Scripts de integracion con Nova (nova-webhook.js, nova_board.py)

**No es la Lambda de Felirni** (Felirni es Python 3.12 con DynamoDB). Probable que sea:
- Backend del board de INTELIGENC(IA) o
- Prototipo Node de integracion Nova-Board

**Accion dia 5 o despues:** auditar esta carpeta para determinar que es y si vale traerlo al repo Nova o a un proyecto separado. No bloquea D2 (que sigue siendo sobre Lambda Python Felirni).

## Addendum — D2 resuelta pre-cierre

**D2 cerrada:** codigo fuente de la Lambda de Felirni bajado desde AWS via `aws lambda get-function` + S3 presigned URL. Archivo unico (handler.py, 1001 lineas, 43KB) en `platform/felirni-api/handler.py`.

Inventario del handler:
- Version 3.0.0 "Atlas outcome-based"
- 31 endpoints: tickets (9), epics (7), sprints (7), people (5), decisions (3), metrics (1)
- Dependencias: solo stdlib + boto3 (ambos provistos por runtime Lambda)
- Config: TABLE_NAME via env var, TENANT y TICKET_PREFIX hardcoded a FELIRNI/FL
- Seguridad: zero secrets hardcoded, CORS habilitado con x-api-key, Authorization

Implicacion dia 5: el tool wrapper `platform/tools/felirni_api.py` puede mapear los 31 endpoints directamente desde el docstring del handler — no hay que adivinar el shape de la API.

Implicacion dia 10+: cuando repliquemos el pattern a CuraPlan/M1/Lorentz, toca parametrizar TENANT y TICKET_PREFIX via env var en lugar de hardcode. Refactor trivial de 2 lineas. Decision: posponer hasta tener 2 instancias operativas para no diseñar en vacio.

## Hallazgo secundario — ia-board-server reclasificado

La carpeta `~/Documents/AWS/ia-board-server/` mencionada en el hallazgo tardio anterior NO es backend de ninguna compania del portfolio. Es Node.js con db.json local, architectura diferente. Probable prototipo personal tuyo o proyecto paralelo. No se integra al repo Nova por ahora.
