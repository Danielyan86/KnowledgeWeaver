#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

STACK_NAME="knowledgeweaver-production"
TEMPLATE_FILE="../templates/main.yaml"
PARAMETERS_FILE="../parameters.json"
REGION=${AWS_REGION:-ap-southeast-2}

echo -e "${YELLOW}🚀 Deploying KnowledgeWeaver Infrastructure with CloudFormation...${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
  echo -e "${RED}❌ AWS CLI not configured. Run: aws configure${NC}"
  exit 1
fi

# Validate template
echo -e "${YELLOW}📋 Validating CloudFormation template...${NC}"
aws cloudformation validate-template \
  --template-body file://$TEMPLATE_FILE \
  --region $REGION \
  > /dev/null

echo -e "${GREEN}✅ Template is valid${NC}"
echo ""

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].StackName' \
  --output text 2>/dev/null || echo "")

if [ -n "$STACK_EXISTS" ]; then
  echo -e "${YELLOW}Stack already exists. Updating...${NC}"
  OPERATION="update-stack"
  WAITER="stack-update-complete"
else
  echo -e "${YELLOW}Creating new stack...${NC}"
  OPERATION="create-stack"
  WAITER="stack-create-complete"
fi

# Deploy stack
echo -e "${YELLOW}🔨 Deploying stack (this will take 15-20 minutes)...${NC}"
aws cloudformation $OPERATION \
  --stack-name $STACK_NAME \
  --template-body file://$TEMPLATE_FILE \
  --parameters file://$PARAMETERS_FILE \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION \
  --tags \
    Key=Project,Value=KnowledgeWeaver \
    Key=ManagedBy,Value=CloudFormation \
    Key=Environment,Value=production

# Wait for completion
echo ""
echo -e "${YELLOW}⏳ Waiting for stack to complete...${NC}"
echo "This will take approximately:"
echo "  - VPC: 2-3 minutes"
echo "  - EKS Cluster: 10-12 minutes"
echo "  - Node Group: 3-5 minutes"
echo "  - Total: 15-20 minutes"
echo ""

aws cloudformation wait $WAITER \
  --stack-name $STACK_NAME \
  --region $REGION

# Get outputs
echo ""
echo -e "${GREEN}✅ Stack deployed successfully!${NC}"
echo ""
echo -e "${YELLOW}📊 Stack Outputs:${NC}"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

# Save outputs to file
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs' \
  --output json > ../outputs.json

echo ""
echo -e "${GREEN}✅ Outputs saved to outputs.json${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Configure kubectl:"
echo "     $(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ConfigureKubectl`].OutputValue' --output text)"
echo ""
echo "  2. Install ALB Controller:"
echo "     cd ../../kubernetes/scripts"
echo "     ./install-alb-controller.sh"
echo ""
echo "  3. Deploy application:"
echo "     ./deploy.sh"
