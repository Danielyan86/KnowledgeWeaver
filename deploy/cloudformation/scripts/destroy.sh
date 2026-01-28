#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

STACK_NAME="knowledgeweaver-production"
REGION=${AWS_REGION:-ap-southeast-2}

echo -e "${RED}⚠️  WARNING: This will destroy ALL infrastructure!${NC}"
echo ""
echo "This includes:"
echo "  - EKS Cluster and all worker nodes"
echo "  - VPC, Subnets, NAT Gateways"
echo "  - ECR Repository (all Docker images)"
echo "  - S3 Bucket (all documents)"
echo "  - CloudWatch Logs"
echo ""
echo -e "${RED}DATA LOSS WARNING: All persistent data will be deleted!${NC}"
echo ""

read -p "Are you absolutely sure? Type 'yes' to confirm: " -r
echo
if [[ ! $REPLY == "yes" ]]; then
  echo "Cancelled."
  exit 0
fi

# Delete stack
echo ""
echo -e "${YELLOW}🗑️  Deleting stack...${NC}"
aws cloudformation delete-stack \
  --stack-name $STACK_NAME \
  --region $REGION

# Wait for deletion
echo -e "${YELLOW}⏳ Waiting for stack deletion (this may take 10-15 minutes)...${NC}"
aws cloudformation wait stack-delete-complete \
  --stack-name $STACK_NAME \
  --region $REGION

echo ""
echo -e "${GREEN}✅ Stack deleted successfully${NC}"
