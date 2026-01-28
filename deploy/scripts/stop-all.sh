#!/bin/bash
set -e

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
PROJECT_ROOT="/Users/sheldon/Github/KnowledgeWeaver"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  KnowledgeWeaver All-in-One Shutdown${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Choose shutdown mode:"
echo ""
echo "1) Quick Stop (recommended)"
echo "   - Stop EKS worker nodes (scale to 0)"
echo "   - Keep infrastructure (VPC, EKS control plane, etc.)"
echo "   - Data preserved in EBS volumes"
echo "   - Quick restart (~5 minutes)"
echo "   - Cost: ~\$73/month (EKS control plane only)"
echo ""
echo "2) Full Destroy"
echo "   - Delete ALL AWS resources"
echo "   - All data will be lost!"
echo "   - No monthly cost"
echo "   - Full redeploy needed (~20 minutes)"
echo ""
echo "3) Cancel"
echo ""

read -p "Enter your choice (1/2/3): " -n 1 -r
echo
echo ""

case $REPLY in
  1)
    # Quick Stop
    echo -e "${YELLOW}🛑 Quick Stop: Stopping EKS worker nodes...${NC}"
    echo ""

    # Get cluster name
    CLUSTER_NAME=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $AWS_REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
      --output text 2>/dev/null || echo "")

    if [ -z "$CLUSTER_NAME" ]; then
      echo -e "${RED}❌ Cluster not found. Nothing to stop.${NC}"
      exit 0
    fi

    # Get node group
    NODEGROUP=$(aws eks list-nodegroups \
      --cluster-name $CLUSTER_NAME \
      --region $AWS_REGION \
      --query 'nodegroups[0]' \
      --output text 2>/dev/null || echo "")

    if [ -z "$NODEGROUP" ]; then
      echo -e "${RED}❌ Node group not found.${NC}"
      exit 0
    fi

    # Scale down to 0
    echo "Scaling node group to 0..."
    aws eks update-nodegroup-config \
      --cluster-name $CLUSTER_NAME \
      --nodegroup-name $NODEGROUP \
      --region $AWS_REGION \
      --scaling-config minSize=0,maxSize=5,desiredSize=0

    echo ""
    echo -e "${GREEN}✅ Worker nodes stopped!${NC}"
    echo ""
    echo "💰 Cost savings:"
    echo "   Before: ~\$228/month (24x7)"
    echo "   After:  ~\$73/month (control plane only)"
    echo "   Saved:  ~\$155/month"
    echo ""
    echo "📊 Infrastructure status:"
    echo "   ✅ VPC - Running (no cost)"
    echo "   ✅ EKS Control Plane - Running (\$73/month)"
    echo "   🛑 Worker Nodes - Stopped (0 nodes)"
    echo "   ✅ Data - Preserved in EBS volumes"
    echo ""
    echo "🚀 To restart:"
    echo "   ./start-all.sh"
    ;;

  2)
    # Full Destroy
    echo -e "${RED}⚠️  FULL DESTROY MODE${NC}"
    echo ""
    echo -e "${RED}This will DELETE ALL resources:${NC}"
    echo "  - EKS Cluster"
    echo "  - VPC and all networking"
    echo "  - ECR Repository (all Docker images)"
    echo "  - S3 Bucket (all documents)"
    echo "  - CloudWatch Logs"
    echo "  - ALL DATA WILL BE LOST!"
    echo ""
    read -p "Type 'DELETE EVERYTHING' to confirm: " -r
    echo

    if [[ ! $REPLY == "DELETE EVERYTHING" ]]; then
      echo "Cancelled."
      exit 0
    fi

    echo ""
    echo -e "${YELLOW}🗑️  Deleting CloudFormation stack...${NC}"
    echo "This will take 10-15 minutes..."
    echo ""

    cd $PROJECT_ROOT/deploy/cloudformation/scripts
    ./destroy.sh

    echo ""
    echo -e "${GREEN}✅ All resources deleted${NC}"
    echo ""
    echo "💰 Monthly cost: \$0"
    echo ""
    echo "🚀 To redeploy:"
    echo "   ./start-all.sh (will take ~20 minutes)"
    ;;

  3)
    # Cancel
    echo "Cancelled."
    exit 0
    ;;

  *)
    echo -e "${RED}Invalid choice. Cancelled.${NC}"
    exit 1
    ;;
esac
