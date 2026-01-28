#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CLUSTER_NAME=${CLUSTER_NAME:-knowledgeweaver}
NODEGROUP_NAME=${NODEGROUP_NAME:-main-nodes}
REGION=${AWS_REGION:-ap-southeast-2}

echo -e "${YELLOW}🚀 Starting KnowledgeWeaver EKS Cluster...${NC}"
echo ""

# 1. Scale up node group
echo -e "${YELLOW}📈 Scaling up node group from 0 to 2...${NC}"
aws eks update-nodegroup-config \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name "$NODEGROUP_NAME" \
  --region "$REGION" \
  --scaling-config minSize=2,maxSize=5,desiredSize=2

# 2. Wait for nodes to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for nodes to be ready (this may take 2-3 minutes)...${NC}"
kubectl wait --for=condition=Ready nodes --all --timeout=300s || {
  echo "Warning: Nodes not ready yet, but continuing..."
}

# 3. Check if resources already exist, if not deploy
echo ""
echo -e "${YELLOW}🔍 Checking if application is deployed...${NC}"
if ! kubectl get namespace prod >/dev/null 2>&1; then
  echo -e "${YELLOW}📦 Deploying application for the first time...${NC}"
  kubectl apply -f ../base/namespace.yaml
  kubectl apply -f ../base/secrets.yaml
  kubectl apply -f ../base/configmap.yaml
  kubectl apply -f ../base/observability/
  kubectl apply -f ../base/neo4j/
  kubectl apply -f ../base/api/
  kubectl apply -f ../base/ingress.yaml
else
  echo -e "${GREEN}✓ Application already deployed${NC}"
fi

# 4. Wait for all pods to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for all pods to be ready...${NC}"
kubectl wait --for=condition=Ready pods --all -n prod --timeout=300s || {
  echo "Warning: Some pods may not be ready yet"
  kubectl get pods -n prod
}

# 5. Get ALB URL
echo ""
echo -e "${YELLOW}🌐 Getting Application Load Balancer URL...${NC}"
ALB_URL=""
for i in {1..30}; do
  ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
  if [ -n "$ALB_URL" ]; then
    break
  fi
  echo "Waiting for ALB to be provisioned... ($i/30)"
  sleep 10
done

echo ""
echo -e "${GREEN}✅ Cluster is ready!${NC}"
echo ""
echo "📊 Access your application:"
echo "   🌐 Main App:    http://$ALB_URL"
echo "   📖 API Docs:    http://$ALB_URL/docs"
echo "   🔍 Phoenix:     http://$ALB_URL/phoenix"
echo "   📈 Langfuse:    http://$ALB_URL/langfuse"
echo ""
echo "💰 Cost: ~\$0.16/hour (2 t3.medium nodes)"
echo "🛑 Don't forget to run ./stop-cluster.sh when done!"
