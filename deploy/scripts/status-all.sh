#!/bin/bash

# Fix AWS profile
export AWS_PROFILE=sheldon2026
unset AWS_DEFAULT_PROFILE
export AWS_REGION=ap-southeast-2

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

STACK_NAME="knowledgeweaver-production"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  KnowledgeWeaver Status Overview${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# CloudFormation Stack Status
echo -e "${YELLOW}📦 CloudFormation Stack:${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
  echo -e "   ${RED}❌ Stack not found${NC}"
  echo ""
  echo "To create infrastructure:"
  echo "   ./start-all.sh"
  exit 0
else
  echo -e "   Status: ${GREEN}$STACK_STATUS${NC}"
fi

# EKS Cluster Status
echo ""
echo -e "${YELLOW}☸️  EKS Cluster:${NC}"
CLUSTER_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [ -n "$CLUSTER_NAME" ]; then
  CLUSTER_STATUS=$(aws eks describe-cluster \
    --name $CLUSTER_NAME \
    --region $AWS_REGION \
    --query 'cluster.status' \
    --output text 2>/dev/null || echo "NOT_FOUND")
  echo -e "   Name: $CLUSTER_NAME"
  echo -e "   Status: ${GREEN}$CLUSTER_STATUS${NC}"
else
  echo -e "   ${YELLOW}⚠️  Not available yet${NC}"
fi

# Node Group Status
echo ""
echo -e "${YELLOW}🖥️  Worker Nodes:${NC}"
if [ -n "$CLUSTER_NAME" ]; then
  NODEGROUP=$(aws eks list-nodegroups \
    --cluster-name $CLUSTER_NAME \
    --region $AWS_REGION \
    --query 'nodegroups[0]' \
    --output text 2>/dev/null || echo "")

  if [ -n "$NODEGROUP" ]; then
    DESIRED_SIZE=$(aws eks describe-nodegroup \
      --cluster-name $CLUSTER_NAME \
      --nodegroup-name $NODEGROUP \
      --region $AWS_REGION \
      --query 'nodegroup.scalingConfig.desiredSize' \
      --output text 2>/dev/null || echo "0")

    MIN_SIZE=$(aws eks describe-nodegroup \
      --cluster-name $CLUSTER_NAME \
      --nodegroup-name $NODEGROUP \
      --region $AWS_REGION \
      --query 'nodegroup.scalingConfig.minSize' \
      --output text 2>/dev/null || echo "0")

    MAX_SIZE=$(aws eks describe-nodegroup \
      --cluster-name $CLUSTER_NAME \
      --nodegroup-name $NODEGROUP \
      --region $AWS_REGION \
      --query 'nodegroup.scalingConfig.maxSize' \
      --output text 2>/dev/null || echo "0")

    if [ "$DESIRED_SIZE" == "0" ]; then
      echo -e "   ${RED}🛑 Stopped${NC} (0 nodes running)"
    else
      echo -e "   ${GREEN}✅ Running${NC} ($DESIRED_SIZE nodes)"
    fi
    echo "   Scaling: Min=$MIN_SIZE, Desired=$DESIRED_SIZE, Max=$MAX_SIZE"
  else
    echo -e "   ${YELLOW}⚠️  Node group not found${NC}"
  fi
else
  echo -e "   ${YELLOW}⚠️  Cluster not available${NC}"
fi

# Kubernetes Pods Status
echo ""
echo -e "${YELLOW}🚀 Kubernetes Pods (namespace: prod):${NC}"
if kubectl get nodes > /dev/null 2>&1; then
  kubectl get pods -n prod 2>/dev/null || echo "   Namespace 'prod' not found"
else
  echo -e "   ${YELLOW}⚠️  Cannot connect to cluster${NC}"
  echo "   Run: aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME"
fi

# Ingress/ALB Status
echo ""
echo -e "${YELLOW}🌐 Application Load Balancer:${NC}"
if kubectl get ingress -n prod > /dev/null 2>&1; then
  ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
  if [ -n "$ALB_URL" ]; then
    echo -e "   ${GREEN}✅ Available${NC}"
    echo "   URL: http://$ALB_URL"
  else
    echo -e "   ${YELLOW}⚠️  Provisioning...${NC}"
  fi
else
  echo -e "   ${YELLOW}⚠️  Not deployed${NC}"
fi

# Cost Estimation
echo ""
echo -e "${YELLOW}💰 Estimated Costs:${NC}"
if [ -n "$DESIRED_SIZE" ] && [ "$DESIRED_SIZE" != "0" ]; then
  NODE_COST=$(echo "$DESIRED_SIZE * 0.08" | bc)
  TOTAL_HOURLY=$(echo "$NODE_COST + 0.09" | bc)  # 0.09 for NAT gateways
  TOTAL_DAILY=$(echo "$TOTAL_HOURLY * 24" | bc)
  echo "   EKS Control Plane: \$73/month (fixed)"
  echo "   Worker Nodes: $DESIRED_SIZE x \$0.08/hour = \$$NODE_COST/hour"
  echo "   NAT Gateways: 2 x \$0.045/hour = \$0.09/hour"
  echo "   Total Hourly: \$$TOTAL_HOURLY/hour"
  echo "   Total Daily: ~\$$TOTAL_DAILY/day"
else
  echo "   EKS Control Plane: \$73/month (fixed)"
  echo "   Worker Nodes: \$0 (stopped)"
  echo "   Total: ~\$73/month"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$DESIRED_SIZE" == "0" ]; then
  echo "🚀 To start services: ./start-all.sh"
elif [ -n "$CLUSTER_NAME" ]; then
  echo "🛑 To stop services: ./stop-all.sh"
else
  echo "🚀 To create infrastructure: ./start-all.sh"
fi
