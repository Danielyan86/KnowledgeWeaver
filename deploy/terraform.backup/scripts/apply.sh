#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Deploying KnowledgeWeaver Infrastructure...${NC}"
echo ""

# Run plan first
echo -e "${YELLOW}📋 Running terraform plan...${NC}"
terraform plan -out=tfplan

echo ""
read -p "Do you want to apply this plan? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  rm -f tfplan
  exit 0
fi

# Apply
echo ""
echo -e "${YELLOW}🔨 Applying terraform plan...${NC}"
terraform apply tfplan
rm -f tfplan

echo ""
echo -e "${GREEN}✅ Infrastructure deployed!${NC}"
echo ""

# Get outputs
echo -e "${YELLOW}📊 Getting outputs...${NC}"
terraform output

echo ""
echo "Next steps:"
echo "  1. Configure kubectl:"
echo "     $(terraform output -raw configure_kubectl)"
echo ""
echo "  2. Install AWS Load Balancer Controller:"
echo "     cd ../../kubernetes/scripts"
echo "     ./install-alb-controller.sh"
echo ""
echo "  3. Deploy application:"
echo "     ./deploy.sh"
