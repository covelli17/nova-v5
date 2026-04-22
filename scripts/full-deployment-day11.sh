#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Atlas Day 11 — Full Deployment Pipeline"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Este script ejecuta:"
echo "  1. Docker build + ECR push"
echo "  2. CloudFormation deployment"
echo "  3. Verificación post-deployment"
echo ""
read -p "¿Continuar? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelado"
    exit 0
fi
echo ""

# Paso 1: Build + Push
echo "════════════════════════════════════════════════════════════════"
echo "  PASO 1/2: Docker Build + ECR Push"
echo "════════════════════════════════════════════════════════════════"
echo ""
bash scripts/build-and-push-day11.sh
echo ""

# Paso 2: CloudFormation Deploy
echo "════════════════════════════════════════════════════════════════"
echo "  PASO 2/2: CloudFormation Deployment"
echo "════════════════════════════════════════════════════════════════"
echo ""
bash scripts/deploy-cloudformation-day11.sh
echo ""

# Resumen final
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETADO"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Próximos pasos:"
echo ""
echo "1. Smoke test en Slack:"
echo "   - Canal: #nova-atlas-sandbox"
echo "   - Comando: @atlas ¿cuál es el estado del board?"
echo "   - Esperar: respuesta en <10s"
echo ""
echo "2. Verificar logs live:"
echo "   aws logs tail /ecs/nova-atlas-listener-prod --follow --region us-east-1"
echo ""
echo "3. Verificar EventBridge schedules:"
echo "   aws events list-rules --name-prefix atlas- --region us-east-1"
echo ""
echo "4. Primera ejecución Monday Kickoff:"
echo "   - Automático: próximo lunes 8am Bogotá"
echo "   - Manual test: invoke Lambda con payload test"
echo ""
