#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

CLUSTER_NAME=${CLUSTER_NAME:-knowledgeweaver}
NODEGROUP_NAME=${NODEGROUP_NAME:-main-nodes}
REGION=${AWS_REGION:-ap-southeast-2}

echo -e "${YELLOW}🛑 Stopping KnowledgeWeaver EKS Cluster...${NC}"
echo ""

# Confirm with user
read -p "This will scale down nodes to 0 (data in Neo4j/Phoenix will be preserved). Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

# Scale down node group
echo -e "${YELLOW}📉 Scaling down node group from 2 to 0...${NC}"
aws eks update-nodegroup-config \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name "$NODEGROUP_NAME" \
  --region "$REGION" \
  --scaling-config minSize=0,maxSize=5,desiredSize=0

echo ""
echo -e "${GREEN}✅ Node group scaled down to 0${NC}"
echo ""
echo "💰 Cost savings: ~\$0.16/hour"
echo "📊 Control plane is still running (\$73/month)"
echo ""
echo "🚀 To restart: ./start-cluster.sh (takes ~5 minutes)"
echo "🗑️  To completely delete: cd ../../terraform && terraform destroy"
