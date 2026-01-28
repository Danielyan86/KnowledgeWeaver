#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CLUSTER_NAME=${CLUSTER_NAME:-knowledgeweaver}
NODEGROUP_NAME=${NODEGROUP_NAME:-main-nodes}
REGION=${AWS_REGION:-ap-southeast-2}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  KnowledgeWeaver EKS Cluster Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Node Group Status
echo -e "${YELLOW}📊 Node Group Status:${NC}"
aws eks describe-nodegroup \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name "$NODEGROUP_NAME" \
  --region "$REGION" \
  --query 'nodegroup.scalingConfig' \
  --output table 2>/dev/null || echo "Node group not found"

echo ""

# Nodes
echo -e "${YELLOW}🖥️  Nodes:${NC}"
kubectl get nodes -o wide 2>/dev/null || echo "No nodes found or cluster not accessible"

echo ""

# Pods
echo -e "${YELLOW}🚀 Pods in 'prod' namespace:${NC}"
kubectl get pods -n prod 2>/dev/null || echo "Namespace 'prod' not found"

echo ""

# Services
echo -e "${YELLOW}🌐 Services:${NC}"
kubectl get services -n prod 2>/dev/null || echo "No services found"

echo ""

# Ingress
echo -e "${YELLOW}🔗 Ingress (ALB):${NC}"
kubectl get ingress -n prod 2>/dev/null || echo "No ingress found"

echo ""

# PVCs
echo -e "${YELLOW}💾 Persistent Volume Claims:${NC}"
kubectl get pvc -n prod 2>/dev/null || echo "No PVCs found"

echo ""

# Cost Estimation
NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
HOURLY_COST=$(echo "$NODE_COUNT * 0.08" | bc)

echo -e "${YELLOW}💰 Cost Estimation:${NC}"
echo "   Nodes running: $NODE_COUNT"
echo "   Hourly cost: \$$HOURLY_COST (nodes only)"
echo "   EKS control plane: \$73/month"
echo ""

if [ "$NODE_COUNT" -eq 0 ]; then
  echo -e "${GREEN}✅ Cluster is stopped (nodes = 0)${NC}"
  echo "   To start: ./start-cluster.sh"
else
  echo -e "${GREEN}✅ Cluster is running${NC}"
  echo "   To stop: ./stop-cluster.sh"
fi
