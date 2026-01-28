#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

STACK_NAME="knowledgeweaver-production"
REGION=${AWS_REGION:-ap-southeast-2}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  KnowledgeWeaver CloudFormation Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if stack exists
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
  echo -e "${RED}❌ Stack not found${NC}"
  echo ""
  echo "To create the stack:"
  echo "  ./deploy.sh"
  exit 0
fi

# Stack status
echo -e "${YELLOW}📦 Main Stack Status:${NC}"
echo "   Status: $STACK_STATUS"

# Nested stacks
echo ""
echo -e "${YELLOW}📚 Nested Stacks:${NC}"
aws cloudformation list-stack-resources \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'StackResourceSummaries[?ResourceType==`AWS::CloudFormation::Stack`].[LogicalResourceId,ResourceStatus]' \
  --output table

# EKS Cluster
echo ""
echo -e "${YELLOW}☸️  EKS Cluster:${NC}"
CLUSTER_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [ -n "$CLUSTER_NAME" ]; then
  aws eks describe-cluster \
    --name $CLUSTER_NAME \
    --region $REGION \
    --query 'cluster.{Name:name,Status:status,Version:version,Endpoint:endpoint}' \
    --output table
else
  echo "   Not yet available"
fi

# Node Group
echo ""
echo -e "${YELLOW}🖥️  Node Group:${NC}"
if [ -n "$CLUSTER_NAME" ]; then
  aws eks list-nodegroups \
    --cluster-name $CLUSTER_NAME \
    --region $REGION \
    --query 'nodegroups[0]' \
    --output text 2>/dev/null || echo "   Not found"

  NODEGROUP=$(aws eks list-nodegroups \
    --cluster-name $CLUSTER_NAME \
    --region $REGION \
    --query 'nodegroups[0]' \
    --output text 2>/dev/null || echo "")

  if [ -n "$NODEGROUP" ]; then
    aws eks describe-nodegroup \
      --cluster-name $CLUSTER_NAME \
      --nodegroup-name $NODEGROUP \
      --region $REGION \
      --query 'nodegroup.{Status:status,DesiredSize:scalingConfig.desiredSize,MinSize:scalingConfig.minSize,MaxSize:scalingConfig.maxSize}' \
      --output table
  fi
else
  echo "   Cluster not ready yet"
fi

# Stack outputs
echo ""
echo -e "${YELLOW}📊 Stack Outputs:${NC}"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

# Cost estimation
echo ""
echo -e "${YELLOW}💰 Estimated Costs:${NC}"
if [ -n "$NODEGROUP" ]; then
  DESIRED_SIZE=$(aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODEGROUP \
    --region $REGION \
    --query 'nodegroup.scalingConfig.desiredSize' \
    --output text 2>/dev/null || echo "0")

  HOURLY_COST=$(echo "$DESIRED_SIZE * 0.08" | bc)
  echo "   EKS Control Plane: \$73/month (fixed)"
  echo "   Worker Nodes: $DESIRED_SIZE x \$0.08/hour = \$$HOURLY_COST/hour"
  echo "   NAT Gateways: 2 x \$0.045/hour = \$0.09/hour"
else
  echo "   Calculating..."
fi
