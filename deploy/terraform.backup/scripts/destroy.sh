#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}⚠️  WARNING: This will destroy ALL infrastructure!${NC}"
echo ""
echo "This includes:"
echo "  - EKS Cluster"
echo "  - All EC2 instances"
echo "  - Load Balancers"
echo "  - NAT Gateways"
echo "  - VPC"
echo "  - S3 Bucket (with all data)"
echo "  - ECR Repositories (with all images)"
echo ""
echo -e "${RED}DATA LOSS WARNING: All persistent data will be deleted!${NC}"
echo ""

read -p "Are you absolutely sure? Type 'yes' to confirm: " -r
echo
if [[ ! $REPLY == "yes" ]]; then
  echo "Cancelled."
  exit 0
fi

echo ""
echo -e "${YELLOW}🗑️  Destroying infrastructure...${NC}"
terraform destroy

echo ""
echo -e "${GREEN}✅ Infrastructure destroyed${NC}"
