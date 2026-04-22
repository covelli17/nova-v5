# Atlas Platform Infrastructure

CloudFormation stack para Atlas PM-Agent: ECS Fargate + EventBridge + Lambda.

## Componentes

- **ECS Cluster**: `nova-atlas-cluster-prod`
- **ECS Service**: 1 Fargate task 24/7 (Slack listener, Socket Mode)
- **Lambda**: scheduled tasks (Monday Kickoff, Daily Stale, Weekly Status)
- **EventBridge**: 3 rules por compañía (Felirni configurado)
- **VPC**: minimal setup con 2 public subnets + Internet Gateway
- **IAM Roles**: task execution, task runtime, lambda, eventbridge
- **CloudWatch Logs**: `/ecs/nova-atlas-listener-prod`, `/aws/lambda/nova-atlas-scheduled-prod`

## Costo estimado

~13 USD/mes (ver `governance/architecture/atlas-multi-company-production.md`)

## Pre-requisitos

### 1. Secret en AWS Secrets Manager

Crear secret `nova/atlas/felirni/config` en us-east-1:

```bash
aws secretsmanager create-secret \
  --name nova/atlas/felirni/config \
  --description "Felirni Atlas configuration" \
  --secret-string '{
    "api_url": "https://le0dj70e7i.execute-api.us-east-1.amazonaws.com/prod",
    "api_key": "ACTUAL_API_KEY_AQUI",
    "slack_bot_token": "xoxb-ACTUAL_TOKEN_AQUI",
    "slack_app_token": "xapp-ACTUAL_TOKEN_AQUI",
    "slack_signing_secret": "ACTUAL_SECRET_AQUI",
    "slack_channel_ops": "#felirni-ops"
  }' \
  --region us-east-1
```

**Obtener valores reales:**
- `api_key`: recuperar desde API Gateway console o SSM Parameter Store
- `slack_bot_token`: Slack App settings → OAuth & Permissions → Bot User OAuth Token
- `slack_app_token`: Slack App settings → Basic Information → App-Level Tokens
- `slack_signing_secret`: Slack App settings → Basic Information → Signing Secret

### 2. ECR Repository + Docker Image

```bash
# Crear repo ECR
aws ecr create-repository \
  --repository-name nova-atlas \
  --region us-east-1

# Build y push (desde raíz del proyecto)
ECR_REPO=$(aws ecr describe-repositories --repository-name nova-atlas --query 'repositories[0].repositoryUri' --output text)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO

docker build -t nova-atlas:latest .
docker tag nova-atlas:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

echo "Image URI: $ECR_REPO:latest"
```

## Deployment

### 1. Validar template

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/atlas-platform.yaml
```

### 2. Deploy stack

```bash
ECR_IMAGE_URI="123456789012.dkr.ecr.us-east-1.amazonaws.com/nova-atlas:latest"

aws cloudformation create-stack \
  --stack-name atlas-platform-prod \
  --template-body file://infrastructure/atlas-platform.yaml \
  --parameters \
      ParameterKey=EcrImageUri,ParameterValue=$ECR_IMAGE_URI \
      ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --tags Key=Project,Value=Nova-Atlas Key=ManagedBy,Value=CloudFormation

# Monitorear progreso
aws cloudformation describe-stack-events \
  --stack-name atlas-platform-prod \
  --region us-east-1 \
  --query 'StackEvents[?ResourceStatus!=`CREATE_COMPLETE`].[Timestamp,ResourceType,ResourceStatus,ResourceStatusReason]' \
  --output table
```

### 3. Verificar deployment

```bash
# Cluster y service
aws ecs describe-clusters --clusters nova-atlas-cluster-prod --region us-east-1
aws ecs describe-services --cluster nova-atlas-cluster-prod --services atlas-listener-prod --region us-east-1

# Lambda
aws lambda get-function --function-name nova-atlas-scheduled-prod --region us-east-1

# EventBridge rules
aws events list-rules --name-prefix atlas- --region us-east-1

# Logs ECS
aws logs tail /ecs/nova-atlas-listener-prod --follow --region us-east-1
```

## Updates

### Actualizar código (nueva imagen Docker)

```bash
# Build y push nueva imagen
docker build -t nova-atlas:v2 .
docker tag nova-atlas:v2 $ECR_REPO:v2
docker push $ECR_REPO:v2

# Update stack con nueva imagen
aws cloudformation update-stack \
  --stack-name atlas-platform-prod \
  --template-body file://infrastructure/atlas-platform.yaml \
  --parameters \
      ParameterKey=EcrImageUri,ParameterValue=$ECR_REPO:v2 \
      ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Force new deployment (sin cambiar template)
aws ecs update-service \
  --cluster nova-atlas-cluster-prod \
  --service atlas-listener-prod \
  --force-new-deployment \
  --region us-east-1
```

### Actualizar Lambda code

```bash
# Build deployment package (desde raíz del proyecto)
cd runtime
pip install -r ../requirements.txt -t package/
cd package && zip -r ../lambda-deploy.zip . && cd ..
zip -g lambda-deploy.zip -r tools/ felirni-api/ mcp_server.py entrypoint.py
cd ..

# Update Lambda
aws lambda update-function-code \
  --function-name nova-atlas-scheduled-prod \
  --zip-file fileb://runtime/lambda-deploy.zip \
  --region us-east-1
```

## Troubleshooting

### ECS task no inicia

```bash
# Ver eventos del service
aws ecs describe-services --cluster nova-atlas-cluster-prod --services atlas-listener-prod --region us-east-1 --query 'services[0].events[0:5]'

# Ver logs del task stopped
TASK_ARN=$(aws ecs list-tasks --cluster nova-atlas-cluster-prod --service-name atlas-listener-prod --desired-status STOPPED --region us-east-1 --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster nova-atlas-cluster-prod --tasks $TASK_ARN --region us-east-1

# Logs CloudWatch
aws logs tail /ecs/nova-atlas-listener-prod --since 10m --region us-east-1
```

### Lambda falla en schedule

```bash
# Ver últimas invocaciones
aws lambda list-invocations --function-name nova-atlas-scheduled-prod --max-items 5 --region us-east-1

# Logs CloudWatch
aws logs tail /aws/lambda/nova-atlas-scheduled-prod --since 1h --region us-east-1
```

## Cleanup

```bash
# Delete stack (destruye todos los recursos excepto logs)
aws cloudformation delete-stack --stack-name atlas-platform-prod --region us-east-1

# Monitorear borrado
aws cloudformation describe-stacks --stack-name atlas-platform-prod --region us-east-1

# Manual cleanup (si es necesario)
aws ecr delete-repository --repository-name nova-atlas --force --region us-east-1
aws secretsmanager delete-secret --secret-id nova/atlas/felirni/config --force-delete-without-recovery --region us-east-1
aws logs delete-log-group --log-group-name /ecs/nova-atlas-listener-prod --region us-east-1
aws logs delete-log-group --log-group-name /aws/lambda/nova-atlas-scheduled-prod --region us-east-1
```

## Próximos pasos

1. ✅ Secret de Felirni en Secrets Manager
2. ✅ ECR repo + primera imagen
3. ✅ Stack deployed
4. ⏳ Smoke test: @atlas responde en #nova-atlas-sandbox
5. ⏳ Primera ejecución Monday Kickoff (próximo lunes 8am)
6. ⏳ Onboarding CuraPlan (agregar secret + EventBridge rules)

## Scaling a nuevas compañías

Para agregar CuraPlan, M1, etc.:

1. Crear secret `nova/atlas/{company}/config` en Secrets Manager
2. Agregar 3 EventBridge rules en el template (Monday, Daily, Weekly)
3. Update stack con `aws cloudformation update-stack`
4. No requiere cambios en código — mismo container/lambda
