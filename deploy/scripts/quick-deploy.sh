#!/bin/bash
set -e

# Quick deploy without building (uses existing ECR image)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="demo"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo -e "${YELLOW}🚀 Quick Deploy (no build)${NC}"
echo ""

cd "$PROJECT_ROOT/deploy/kubernetes/base"

kubectl apply -f configmap.yaml
kubectl apply -f neo4j/
kubectl apply -f observability/postgres/
kubectl apply -f observability/phoenix/
kubectl apply -f api/

kubectl rollout restart deployment/api -n "$NAMESPACE"

echo ""
echo -e "${GREEN}✅ Deployed!${NC}"
kubectl get pods -n "$NAMESPACE"
