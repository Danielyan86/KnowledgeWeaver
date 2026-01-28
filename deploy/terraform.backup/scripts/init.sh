#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
echo ""

# Check if terraform.tfvars exists
if [ ! -f terraform.tfvars ]; then
  echo -e "${YELLOW}⚠️  terraform.tfvars not found. Creating from example...${NC}"
  cp terraform.tfvars.example terraform.tfvars
  echo -e "${YELLOW}📝 Please edit terraform.tfvars and update the values${NC}"
  exit 1
fi

# Initialize Terraform
echo -e "${YELLOW}📦 Running terraform init...${NC}"
terraform init

echo ""
echo -e "${GREEN}✅ Terraform initialized${NC}"
echo ""
echo "Next steps:"
echo "  1. Review terraform.tfvars"
echo "  2. Run: terraform plan"
echo "  3. Run: terraform apply"
