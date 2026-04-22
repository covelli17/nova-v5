#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Atlas Day 11 — CloudFormation Deployment"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Variables
STACK_NAME="atlas-platform-prod"
TEMPLATE_FILE="infrastructure/atlas-platform.yaml"
ECR_IMAGE_URI="105045465301.dkr.ecr.us-east-1.amazonaws.com/nova-atlas:day11"
REGION="us-east-1"
ENV="prod"

# 1. Validar template
echo "📋 Validando CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION > /dev/null
echo "✅ Template válido"
echo ""

# 2. Verificar si stack ya existe
echo "🔍 Verificando si stack existe..."
if aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION > /dev/null 2>&1; then
    echo "⚠️  Stack $STACK_NAME ya existe"
    echo ""
    read -p "¿Actualizar stack existente? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelado"
        exit 0
    fi
    
    ACTION="update-stack"
    echo "🔄 Actualizando stack..."
else
    ACTION="create-stack"
    echo "🆕 Creando nuevo stack..."
fi
echo ""

# 3. Deploy stack
echo "🚀 Deploying stack: $STACK_NAME"
echo "   Template: $TEMPLATE_FILE"
echo "   Image: $ECR_IMAGE_URI"
echo "   Environment: $ENV"
echo ""

aws cloudformation $ACTION \
    --stack-name $STACK_NAME \
    --template-body file://$TEMPLATE_FILE \
    --parameters \
        ParameterKey=EcrImageUri,ParameterValue=$ECR_IMAGE_URI \
        ParameterKey=Environment,ParameterValue=$ENV \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --tags \
        Key=Project,Value=Nova-Atlas \
        Key=ManagedBy,Value=CloudFormation \
        Key=Environment,Value=$ENV

echo ""
echo "⏳ Esperando a que el stack esté listo..."
echo "   (Esto puede tomar 5-10 minutos)"
echo ""

# 4. Monitorear progreso
if [ "$ACTION" == "create-stack" ]; then
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region $REGION
else
    aws cloudformation wait stack-update-complete \
        --stack-name $STACK_NAME \
        --region $REGION
fi

echo "✅ Stack deployment completado"
echo ""

# 5. Mostrar outputs
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table
echo ""

# 6. Verificar ECS service
echo "🔍 Verificando ECS service..."
CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
    --output text)

SERVICE_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ServiceName`].OutputValue' \
    --output text)

echo "   Cluster: $CLUSTER_NAME"
echo "   Service: $SERVICE_NAME"
echo ""

aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].[serviceName,status,runningCount,desiredCount]' \
    --output table
echo ""

# 7. Mostrar logs recientes
echo "📋 Logs recientes (últimos 5 minutos):"
LOG_GROUP="/ecs/nova-atlas-listener-$ENV"
echo "   Log Group: $LOG_GROUP"
echo ""
aws logs tail $LOG_GROUP --since 5m --region $REGION | head -50
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Deployment completado exitosamente"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Próximos pasos:"
echo "  1. Verificar logs: aws logs tail $LOG_GROUP --follow"
echo "  2. Smoke test en Slack: @atlas en #nova-atlas-sandbox"
echo "  3. Verificar EventBridge schedules activos"
echo ""
