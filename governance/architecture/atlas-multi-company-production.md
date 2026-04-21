# Atlas Multi-Company Production — Architecture

**Status:** aprobado 2026-04-20
**Owner:** Santi
**Review cadence:** mensual o antes de onboardear compania nueva

## Objetivo

Plataforma unica que corre Atlas como PM-Agent operativo para las 7 companias del grupo SC17 (Felirni, CuraPlan, M1, Lorentz, INTELIGENCIA, Lulo, Robot Land) con:

1. Slack bot listener que responde a menciones en el canal de cada compania
2. Schedules programados (Monday Kickoff, daily status, weekly review)
3. Escrituras controladas a los dashboards de cada compania via API Gateway
4. Costo bajo (10-15 USD/mes total) y una sola plataforma que mantener

## Decision arquitectonica

**Opcion elegida: AWS ECS Fargate + EventBridge Scheduler + Lambda.**

Alternativas evaluadas y descartadas:

| Opcion | Razon de descarte |
|---|---|
| Mac Santiago + launchd | No escala, no soporta Slack Socket Mode, muere al cerrar laptop |
| Solo Lambda + EventBridge | Lambda no mantiene conexiones WebSocket persistentes |
| Railway / Fly.io | Segunda plataforma operativa, mas caro a escala de 7 companias |
| Solo Fargate (sin Lambda) | Overhead innecesario para schedules que son workloads cortos |

## Componentes

### 1. ECS Fargate Service — Slack Listener

Task persistente con conexion Socket Mode a Slack.

- **CPU/Memory:** 0.25 vCPU / 512 MB
- **Scaling:** desired count fijo en 1
- **Image:** Docker desde repo Nova v5, publicada a ECR
- **Secrets:** via Secrets Manager
- **Networking:** solo egress, cero ingress publico

Responsabilidades:
- Escucha menciones @atlas en canales de companias registradas
- Identifica compania segun canal (#felirni-ops -> Felirni)
- Carga companies/{company}/context.md + outcomes/{company}/atlas/prompt.md
- Ejecuta agente y responde en el thread

### 2. Lambda nova-atlas-scheduled

Workload corto invocado por EventBridge con payload {company, task_type}.

- **Runtime:** Python 3.12
- **Handler:** mismo codigo base que Fargate, modo scheduled
- **Timeout:** 5 min
- **Secrets:** mismos que Fargate via Secrets Manager

Responsabilidades:
- Monday Kickoff cada lunes 8am por compania
- Status semanal cada viernes 5pm
- Detectar tareas vencidas diario 9am

### 3. EventBridge Scheduler

Reglas cron por compania (3 rules x 7 companias = 21 rules):

- atlas-monday-kickoff-{company}: cron(0 13 ? * MON *)
- atlas-daily-stale-{company}: cron(0 14 ? * * *)
- atlas-weekly-status-{company}: cron(0 22 ? * FRI *)

Horas en UTC. Bogota UTC-5, entonces 13 UTC = 8am Bogota.

### 4. Secrets Manager

Un secret por compania con estructura:

- nova/atlas/felirni/config
  - api_base_url
  - api_key
  - slack_bot_token
  - slack_app_token (Socket Mode)
  - slack_channel_ops
  - slack_channel_alerts

- nova/atlas/curaplan/config (misma estructura)

Permite rotacion independiente por compania. IAM policy del ECS task y Lambda solo permite leer secrets con prefijo nova/atlas/.

### 5. ECR

Repositorio nova-atlas guarda imagenes Docker versionadas. Deploy = push nueva imagen + update service.

## Estructura del repo Nova v5
outcomes/
felirni/atlas/
curaplan/atlas/
m1/atlas/
...
platform/
atlas-runtime/
Dockerfile
entrypoint.py           # modo listener o scheduled segun env var
slack_listener.py
scheduled_runner.py
company_loader.py
tools/
felirni_api.py
curaplan_api.py
slack_bot.py
secrets_manager.py
infrastructure/
atlas-platform.yaml       # CloudFormation ECS + Lambda + IAM
scheduler-rules.yaml      # EventBridge rules por compania
secrets-bootstrap.md
governance/
architecture/
atlas-multi-company-production.md
security/

## Flujos operacionales

### Flujo 1: mencion en Slack

1. Usuario escribe "@atlas status tarea FL-042" en #felirni-ops
2. Slack envia evento via Socket Mode al Fargate task
3. slack_listener identifica: canal=felirni-ops -> company=felirni
4. company_loader carga context.md + prompt.md de Felirni
5. Atlas corre con claude-agent-sdk, usa tool felirni_api
6. Respuesta en el thread del mensaje original

### Flujo 2: Monday Kickoff automatico

1. EventBridge dispara 13:00 UTC lunes
2. Invoca Lambda con {company: "felirni", task: "monday_kickoff"}
3. Lambda carga contexto, consulta API para estado actual
4. Genera kickoff markdown
5. Postea en #felirni-ops via slack_bot

### Flujo 3: agregar compania nueva (ej Lorentz)

1. Crear companies/lorentz/context.md
2. Fork outcomes/lorentz/atlas/ desde Felirni
3. Agregar platform/tools/lorentz_api.py
4. Crear secret nova/atlas/lorentz/config
5. Agregar 3 EventBridge rules
6. Crear #lorentz-ops e invitar @atlas
7. Deploy: docker build + push + ECS update

Zero cambio estructural.

## Costos proyectados (7 companias activas)

| Servicio | Uso | Costo mensual USD |
|---|---|---|
| ECS Fargate 0.25 vCPU / 512 MB 24/7 | 1 task continuo | 8.50 |
| Lambda scheduled runs | ~630 invocaciones/mes | 0 (free tier) |
| EventBridge rules | 21 rules activas | 0 (free tier) |
| DynamoDB | Ya pagado por companias | 0 incremental |
| Secrets Manager | 7 secrets x 0.40 | 2.80 |
| CloudWatch Logs | ~2 GB/mes total | ~1 |
| ECR | <500 MB | 0 (primer GB free) |
| Data transfer | Egress a Slack y APIs | <1 |
| **TOTAL** | | **~13 USD/mes** |

Comparado con Railway a escala de 7 bots: ~25 USD/mes con menos observability.

## Modelo de seguridad

1. **Least privilege IAM:** task role solo puede leer secrets nova/atlas/* e invocar Lambdas registradas. Cero acceso a otros recursos.
2. **Secrets nunca en codigo ni logs:** Secrets Manager con rotacion manual. Codigo lee en runtime con cache en memoria.
3. **Network isolation:** Fargate en subnet privada, solo egress via NAT Gateway o VPC endpoints.
4. **Slack allowlist:** listener valida canal registrado. Si aparece en canal no registrado, loguea y responde "no configurado".
5. **Confirmacion humana en escrituras sensibles:** Atlas nunca hace delete o status=cancelled sin reaccion humana (check/x) en Slack.
6. **Guardian checkpoint antes de cada deploy:** sin docker push ni cloudformation deploy sin Guardian audit.
7. **Rate limiting:** max 20 invocaciones/min por compania.

## Roadmap ejecucion

| Dia | Entregable | Done criteria |
|---|---|---|
| 5 | Tool wrappers felirni_api, slack_bot, secrets_manager. Tests. Guardian check. | pytest pasa. Risk Score <30. |
| 6 | Dockerfile + entrypoint modo scheduled. Secret de Felirni. Smoke test local. | Mensaje llega a canal de prueba. |
| 7 | CloudFormation stack atlas-platform deployado. Primer schedule live. | ECS task RUNNING. EventBridge rule armada. |
| 8 | Fargate listener operativo. Slack bot responde en <10s. | @atlas responde 3 preguntas distintas OK. |
| 9 | CuraPlan onboarded. | Atlas opera CuraPlan con mismo deploy. |
| 10-12 | M1, Lorentz, INTELIGENCIA, Lulo, Robot Land. | 7 companias operativas. |

## Riesgos conocidos

1. **Socket Mode sobre Fargate:** si task reinicia se corta conexion temporalmente. Mitigacion: health check fuerza reconexion, Slack reintenta hasta 3 veces.
2. **Drift del prompt base entre companias:** cuando mejoremos Atlas base, hay que propagar. Mitigacion: dia 10 introducir outcomes/_base/atlas/prompt.md con inheritance via overlays.
3. **PII en logs CloudWatch:** Atlas puede loguear contexto con data sensible. Mitigacion: filter en logger antes de escribir (dia 6).
4. **Token Slack comprometido = blast radius 7 workspaces si comparten token.** Mitigacion: un Slack App por compania, tokens separados.

## Decisiones abiertas

- **D1 RESUELTA 2026-04-20 noche:** una Slack App por compania en workspace propio. Tokens separados. Blast radius aislado por compania. Felirni App ya existe (creada 18 abril).
- **D2:** recuperar codigo fuente de la Lambda de Felirni (no esta en Mac Santiago). Resolver dia 5.
- **D3:** cluster ECS nuevo nova-atlas-cluster o reutilizar existente. Resolver dia 6.
- **D4:** canal de prueba para smoke test dia 6. Proponer #nova-atlas-sandbox. Resolver dia 6.

## Referencias

- Backend M1/Felirni: ~/Proyectos/M1/docs/GUIA-DEPLOY-BOARD-SC17.md
- Session dia 3 (Atlas Felirni local): governance/sessions/2026-04-19-dia3-atlas-felirni.md
- Session dia 4 (seguridad + este doc): governance/sessions/2026-04-20-dia4-security-and-production-plan.md
