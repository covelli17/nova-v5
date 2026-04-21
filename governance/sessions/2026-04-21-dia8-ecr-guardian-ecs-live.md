# Sesión Día 8 — ECR + Guardian + ECS Live
**Fecha:** 2026-04-21
**Mac:** Lulo (scovelli@MacBook-Lulo-Santiago)
**HEAD:** 1971dc2

## Commits del día
- 666198d: security fixes Guardian + ECR + Secrets Manager
- 1971dc2: slack_bot.main() módulo-level + asyncio.run + amd64 build

## Logros
- API key nova-atlas-prod actualizada en Mac Lulo
- Docker Desktop instalado en Mac Lulo
- ECR repo nova-atlas creado: 105045465301.dkr.ecr.us-east-1.amazonaws.com/nova-atlas
- Docker build --platform linux/amd64 (fix crítico ARM→amd64 para Fargate)
- Secrets Manager nova/atlas/felirni/config poblado (5 keys)
- CloudFormation stack atlas-platform: CREATE_COMPLETE
- Guardian Risk Score: 2 Críticos + 7 Altos cerrados
- Tests: 101 PASSED
- ECS Service atlas-felirni: Running=1 ✅ Atlas en producción

## Fixes Guardian cerrados
- NG-001 (Critica): bypassPermissions → allowlisted + untrusted_input
- NG-003 (Alta): Lambda auth hmac.compare_digest
- NG-004 (Alta): run_bash allowlist sin intérpretes
- NG-005 (Alta): slack_bot delimitador untrusted_slack_message
- NG-006 (Alta): .dockerignore creado
- NG-007 (Alta): output LLM sanitizado
- NG-009 (Alta): disclaimer médico en prompt Atlas

## Bugs de arranque resueltos
- slack_bot.main() estaba dentro de __name__==__main__ (no importable)
- entrypoint.py no hacía asyncio.run() en coroutines
- Docker image era ARM64, Fargate requiere amd64

## Deuda técnica abierta
- NG-002: .envrc con keys en texto plano (local, no en repo)
- NG-008: PII encryption arquitectural (Ley 1581)
- ECS Service falta en CloudFormation template (creado vía CLI)
- M-3: client leak felirni_api + slack_bot bajo carga

## Prioridad día 9
1. Smoke test Atlas en #nova-atlas-sandbox (mención en Slack)
2. Agregar AWS::ECS::Service al atlas-platform.yaml
3. Configurar EXPECTED_API_KEY en Lambda env vars
4. Verificar logs /nova/atlas sin errores post-arranque

## Fix post-cierre
- IAM: nova-atlas-task-role sin permiso secretsmanager:GetSecretValue → agregado vía put-role-policy
- Resource: arn:aws:secretsmanager:us-east-1:105045465301:secret:nova/atlas/*
- Atlas online: bot_id=B0ATML6JFNY, socket_mode conectado ✅
- Pendiente día 9: mover esta policy al CloudFormation template
