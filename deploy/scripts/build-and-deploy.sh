#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
AWS_REGION="ap-southeast-2"
CLUSTER_NAME="knowledgeweaver-production"
ECR_REPO="858766041545.dkr.ecr.${AWS_REGION}.amazonaws.com/knowledgeweaver-api"
NAMESPACE="demo"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  KnowledgeWeaver Build & Deploy${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Step 1: Build Docker image
echo -e "${YELLOW}📦 Building Docker image...${NC}"
cd "$PROJECT_ROOT"

aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_REPO"

docker buildx build \
  --platform linux/amd64 \
  -t "${ECR_REPO}:latest" \
  -t "${ECR_REPO}:$(date +%Y%m%d-%H%M%S)" \
  -f deploy/docker/api/Dockerfile \
  . \
  --push

echo -e "${GREEN}✅ Docker image built and pushed${NC}"
echo ""

# Step 2: Configure kubectl
echo -e "${YELLOW}⚙️  Configuring kubectl...${NC}"
aws eks update-kubeconfig \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME"

echo -e "${GREEN}✅ kubectl configured${NC}"
echo ""

# Step 3: Create/update secrets
echo -e "${YELLOW}🔐 Creating secrets...${NC}"
cd "$PROJECT_ROOT/deploy/kubernetes/scripts"
bash create-secrets.sh

echo ""

# Step 4: Deploy Kubernetes resources
echo -e "${YELLOW}🚀 Deploying Kubernetes resources...${NC}"
cd "$PROJECT_ROOT/deploy/kubernetes/base"

# Apply in order
kubectl apply -f configmap.yaml
kubectl apply -f neo4j/
kubectl apply -f observability/postgres/
kubectl apply -f observability/phoenix/
kubectl apply -f api/

echo -e "${GREEN}✅ Resources deployed${NC}"
echo ""

# Step 5: Restart deployment to pull new image
echo -e "${YELLOW}🔄 Restarting API deployment...${NC}"
kubectl rollout restart deployment/api -n "$NAMESPACE"
kubectl rollout status deployment/api -n "$NAMESPACE" --timeout=120s

echo -e "${GREEN}✅ API deployment restarted${NC}"
echo ""

# Step 6: Show deployment status
echo -e "${YELLOW}📊 Deployment Status:${NC}"
echo ""
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get svc -n "$NAMESPACE"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Check pod logs: kubectl logs -n $NAMESPACE deployment/api"
echo "2. Check Neo4j: kubectl logs -n $NAMESPACE neo4j-0"
echo "3. Port forward API: kubectl port-forward -n $NAMESPACE svc/api 9621:80"
echo ""
