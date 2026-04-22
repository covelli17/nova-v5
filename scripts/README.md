# Deployment Scripts — Día 11

Scripts para deployment completo de Atlas a AWS.

## Pre-requisitos

✅ Docker Desktop corriendo
✅ AWS CLI configurado (profile m1-deploy-user)
✅ Secret `nova/atlas/felirni/config` en Secrets Manager
✅ ECR repository `nova-atlas` creado

## Ejecución paso a paso

### 1. Build + Push a ECR

```bash
bash scripts/build-and-push-day11.sh
```

**Duración:** ~5-10 minutos

**Acciones:**
- Verifica Docker daemon
- Login a ECR
- Build imagen (platform: linux/amd64)
- Tag: day11 + latest
- Push a ECR
- Verificación

**Output esperado:**
```
✅ Build + Push completado exitosamente
Imagen URI: 105045465301.dkr.ecr.us-east-1.amazonaws.com/nova-atlas:day11
```

### 2. Deploy CloudFormation Stack

```bash
bash scripts/deploy-cloudformation-day11.sh
```

**Duración:** ~5-10 minutos

**Acciones:**
- Valida template CloudFormation
- Crea/actualiza stack atlas-platform-prod
- Espera a CREATE_COMPLETE/UPDATE_COMPLETE
- Muestra outputs del stack
- Verifica ECS service status
- Muestra logs recientes

**Output esperado:**
```
✅ Deployment completado exitosamente
ECS Service: ACTIVE, runningCount: 1, desiredCount: 1
```

### 3. Pipeline completo (opcional)

```bash
bash scripts/full-deployment-day11.sh
```

Ejecuta build + push + deploy en secuencia.

## Verificación post-deployment

### ECS Task Status

```bash
aws ecs describe-services \
  --cluster nova-atlas-cluster-prod \
  --services atlas-listener-prod \
  --region us-east-1
```

### CloudWatch Logs (live)

```bash
aws logs tail /ecs/nova-atlas-listener-prod --follow --region us-east-1
```

### Slack Smoke Test

1. Ir a #nova-atlas-sandbox en Felirni workspace
2. Mencionar: `@atlas ¿cuál es el estado del board?`
3. Esperar respuesta en <10s

### EventBridge Schedules

```bash
aws events list-rules --name-prefix atlas- --region us-east-1
```

## Troubleshooting

### Docker daemon no responde

```bash
# Reiniciar Docker Desktop
# Esperar 30-60s
docker info  # Verificar
```

### ECS task no inicia

```bash
# Ver logs del task
aws logs tail /ecs/nova-atlas-listener-prod --since 10m --region us-east-1

# Ver eventos del service
aws ecs describe-services \
  --cluster nova-atlas-cluster-prod \
  --services atlas-listener-prod \
  --region us-east-1 \
  --query 'services[0].events[0:5]'
```

### Stack creation failed

```bash
# Ver eventos del stack
aws cloudformation describe-stack-events \
  --stack-name atlas-platform-prod \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus!=`CREATE_COMPLETE`]' \
  --output table

# Rollback
aws cloudformation delete-stack \
  --stack-name atlas-platform-prod \
  --region us-east-1
```

## Rollback completo

```bash
# 1. Delete stack
aws cloudformation delete-stack --stack-name atlas-platform-prod --region us-east-1

# 2. Esperar a DELETE_COMPLETE
aws cloudformation wait stack-delete-complete \
  --stack-name atlas-platform-prod \
  --region us-east-1

# 3. (Opcional) Delete ECR images
aws ecr batch-delete-image \
  --repository-name nova-atlas \
  --image-ids imageTag=day11 \
  --region us-east-1
```

## Costo estimado

- **Primeras 24h:** <$0.10 USD
- **Mensual:** ~$13 USD (7 compañías)

## Logs de sesión

Todos los pasos documentados en:
- `governance/sessions/2026-04-22-dia11-inicio.md`
- `governance/sessions/2026-04-22-dia11-cierre.md` (post-deployment)
