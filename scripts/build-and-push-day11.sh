#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Atlas Day 11 — Docker Build + ECR Push"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Variables
ECR_REPO="105045465301.dkr.ecr.us-east-1.amazonaws.com/nova-atlas"
REGION="us-east-1"
TAG="day11"

# 1. Verificar Docker daemon
echo "📋 Verificando Docker daemon..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ ERROR: Docker daemon no está corriendo"
    echo "   Por favor inicia Docker Desktop y vuelve a ejecutar este script"
    exit 1
fi
echo "✅ Docker daemon OK"
echo ""

# 2. ECR Login
echo "🔐 Autenticando con ECR..."
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ECR_REPO
echo "✅ ECR login OK"
echo ""

# 3. Build imagen
echo "🔨 Building Docker image..."
echo "   Platform: linux/amd64"
echo "   Tag: nova-atlas:$TAG"
docker build --platform linux/amd64 -t nova-atlas:$TAG .
echo "✅ Build completado"
echo ""

# 4. Tag para ECR
echo "🏷️  Tagging imagen..."
docker tag nova-atlas:$TAG $ECR_REPO:$TAG
docker tag nova-atlas:$TAG $ECR_REPO:latest
echo "✅ Tagged: $ECR_REPO:$TAG"
echo "✅ Tagged: $ECR_REPO:latest"
echo ""

# 5. Push a ECR
echo "⬆️  Pushing a ECR..."
echo "   Imagen 1: $ECR_REPO:$TAG"
docker push $ECR_REPO:$TAG
echo ""
echo "   Imagen 2: $ECR_REPO:latest"
docker push $ECR_REPO:latest
echo "✅ Push completado"
echo ""

# 6. Verificar
echo "🔍 Verificando imagen en ECR..."
aws ecr describe-images \
    --repository-name nova-atlas \
    --image-ids imageTag=$TAG \
    --region $REGION \
    --query 'imageDetails[0].[imagePushedAt,imageSizeInBytes,imageTags]' \
    --output table
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Build + Push completado exitosamente"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Imagen URI: $ECR_REPO:$TAG"
echo ""
echo "Próximo paso:"
echo "  bash scripts/deploy-cloudformation-day11.sh"
echo ""
