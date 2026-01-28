#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📦 Deploying KnowledgeWeaver to Kubernetes...${NC}"
echo ""

# Apply resources in order
echo -e "${YELLOW}1. Creating namespace...${NC}"
kubectl apply -f ../base/namespace.yaml

echo -e "${YELLOW}2. Applying secrets and configmap...${NC}"
kubectl apply -f ../base/secrets.yaml
kubectl apply -f ../base/configmap.yaml

echo -e "${YELLOW}3. Deploying observability services...${NC}"
echo "   - PostgreSQL"
kubectl apply -f ../base/observability/postgres/

echo "   - Phoenix"
kubectl apply -f ../base/observability/phoenix/

echo "   - Langfuse"
kubectl apply -f ../base/observability/langfuse/

echo -e "${YELLOW}4. Deploying Neo4j...${NC}"
kubectl apply -f ../base/neo4j/

echo -e "${YELLOW}5. Deploying API...${NC}"
kubectl apply -f ../base/api/

echo -e "${YELLOW}6. Deploying Ingress (ALB)...${NC}"
kubectl apply -f ../base/ingress.yaml

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Check status:"
echo "   kubectl get pods -n prod"
echo "   kubectl get services -n prod"
echo "   kubectl get ingress -n prod"
echo ""
echo "⏳ Wait for all pods to be ready:"
echo "   kubectl wait --for=condition=Ready pods --all -n prod --timeout=300s"
