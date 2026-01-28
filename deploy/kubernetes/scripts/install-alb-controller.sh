#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔧 Installing AWS Load Balancer Controller...${NC}"
echo ""

# Get cluster name and region
CLUSTER_NAME=$(kubectl config current-context | cut -d'/' -f2 | cut -d'.' -f1)
REGION=${AWS_REGION:-ap-southeast-2}

echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo ""

# Add Helm repo
echo -e "${YELLOW}1. Adding eks-charts Helm repository...${NC}"
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Create service account
echo -e "${YELLOW}2. Creating service account...${NC}"
kubectl create serviceaccount aws-load-balancer-controller -n kube-system --dry-run=client -o yaml | kubectl apply -f -

# Get ALB controller role ARN from Terraform output
ALB_ROLE_ARN=$(cd ../../../terraform && terraform output -raw eks_alb_controller_role_arn 2>/dev/null || echo "")

if [ -z "$ALB_ROLE_ARN" ]; then
  echo -e "${YELLOW}⚠️  Could not get ALB role ARN from Terraform. You'll need to annotate the service account manually.${NC}"
else
  echo -e "${YELLOW}3. Annotating service account with IAM role...${NC}"
  kubectl annotate serviceaccount -n kube-system aws-load-balancer-controller \
    eks.amazonaws.com/role-arn=$ALB_ROLE_ARN --overwrite
fi

# Install ALB controller using Helm
echo -e "${YELLOW}4. Installing AWS Load Balancer Controller via Helm...${NC}"
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=$REGION \
  --set vpcId=$(cd ../../../terraform && terraform output -raw vpc_id 2>/dev/null || echo "")

echo ""
echo -e "${YELLOW}5. Waiting for controller to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system --timeout=120s

echo ""
echo -e "${GREEN}✅ AWS Load Balancer Controller installed!${NC}"
echo ""
echo "Verify installation:"
echo "  kubectl get deployment -n kube-system aws-load-balancer-controller"
