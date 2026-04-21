# Dia 7 - Secrets Manager + CLI Runner + CloudFormation

## Estado al cierre
- HEAD: ver git log --oneline -1
- Guardian Risk Score: 0 Criticos en repo, 0 Altos en codigo
- Tests: 101 PASSED en ambos Macs (Santiago + Lulo)

## Entregables cerrados

### Bloque 1: secrets_manager canonico
- get_felirni_config() shortcut para nova/atlas/felirni/config
- invalidate() selectivo o total
- 11/11 tests PASSED
- runtime/secrets_manager.py viejo con clave hostname eliminado

### Bloque 2: cli_runner.py
- Loop tool_use completo con historial
- 8 tools via call_tool canonico del mcp_server
- Smoke test OK: Atlas CLI responde en espanol en MacBook Lulo
- get_secret() firma invalida corregida en mcp_server.py

### Bloque 3: CloudFormation atlas-platform.yaml
- ECS Fargate 512cpu/1024mb
- IAM roles con least privilege (Secrets Manager + DynamoDB)
- validate-template OK

## Seguridad (Guardian dia 7)
- C-1: .envrc symlink removido del tracking git
- C-2: secrets_manager con clave hostname eliminado
- A-3: shell=False en mcp_server.py
- A-4: CORS wildcard restringido a API Gateway origin
- A-5: stack traces removidos de respuestas 500
- A-6: get_secret() firma invalida -> get_felirni_config()
- A-7: USER nobody en Dockerfile

## Deuda tecnica abierta
- M-3 felirni_api: client leak sin context manager
- M-3 slack_bot: ClaudeSDKClient nuevo por mensaje bajo carga
- B-2/B-3 secrets_manager: sin allowlist + tracebacks suprimidos
- C-1 envrc local en Mac Lulo: key vieja (no bloquea, fuera del repo)

## Dia 8 - prioridades
1. ECR repo + docker push nova-atlas:day7
2. CloudFormation deploy (necesita VpcId + SubnetIds)
3. Secret nova/atlas/felirni/config poblado en AWS Secrets Manager
4. ECS Service live con slack_listener
