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
NC='\033[0m'

echo -e "${YELLOW}🔍 Validating all CloudFormation templates...${NC}"
echo ""

# Validate VPC
echo -e "${YELLOW}1. Validating VPC template...${NC}"
aws cloudformation validate-template \
  --template-body file://../templates/vpc.yaml \
  --region $AWS_REGION \
  > /dev/null && echo -e "${GREEN}✅ VPC template is valid${NC}"

# Validate EKS
echo -e "${YELLOW}2. Validating EKS template...${NC}"
aws cloudformation validate-template \
  --template-body file://../templates/eks.yaml \
  --region $AWS_REGION \
  > /dev/null && echo -e "${GREEN}✅ EKS template is valid${NC}"

# Validate ECR
echo -e "${YELLOW}3. Validating ECR template...${NC}"
aws cloudformation validate-template \
  --template-body file://../templates/ecr.yaml \
  --region $AWS_REGION \
  > /dev/null && echo -e "${GREEN}✅ ECR template is valid${NC}"

# Validate S3
echo -e "${YELLOW}4. Validating S3 template...${NC}"
aws cloudformation validate-template \
  --template-body file://../templates/s3.yaml \
  --region $AWS_REGION \
  > /dev/null && echo -e "${GREEN}✅ S3 template is valid${NC}"

# Validate CloudWatch
echo -e "${YELLOW}5. Validating CloudWatch template...${NC}"
aws cloudformation validate-template \
  --template-body file://../templates/cloudwatch.yaml \
  --region $AWS_REGION \
  > /dev/null && echo -e "${GREEN}✅ CloudWatch template is valid${NC}"

# Validate Main
echo -e "${YELLOW}6. Validating Main template...${NC}"
aws cloudformation validate-template \
  --template-body file://../templates/main.yaml \
  --region $AWS_REGION \
  > /dev/null && echo -e "${GREEN}✅ Main template is valid${NC}"

echo ""
echo -e "${GREEN}✅ All templates are valid!${NC}"
echo ""
echo "Next step: Run ./deploy.sh to create the infrastructure"
