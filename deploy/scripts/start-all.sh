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
AUTO_CONFIRM=${AUTO_CONFIRM:-no}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  KnowledgeWeaver All-in-One Startup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Check if CloudFormation stack exists
echo -e "${YELLOW}📦 Step 1: Checking CloudFormation stack...${NC}"
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" == "NOT_FOUND" ]; then
  echo -e "${YELLOW}⚠️  Stack not found. Creating new infrastructure...${NC}"
  if [ "$AUTO_CONFIRM" != "yes" ]; then
    echo -e "${RED}This will take 15-20 minutes. Continue? (y/N)${NC}"
    read -p "" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Cancelled."
      exit 0
    fi
  else
    echo -e "${GREEN}✅ AUTO_CONFIRM=yes, proceeding...${NC}"
  fi

  cd $PROJECT_ROOT/deploy/cloudformation/scripts
  ./deploy.sh

elif [ "$STACK_STATUS" == "CREATE_COMPLETE" ] || [ "$STACK_STATUS" == "UPDATE_COMPLETE" ]; then
  echo -e "${GREEN}✅ Stack already exists: $STACK_STATUS${NC}"

  # Check if nodes are running
  CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
    --output text 2>/dev/null || echo "")

  if [ -n "$CLUSTER_NAME" ]; then
    NODEGROUP=$(aws eks list-nodegroups \
      --cluster-name $CLUSTER_NAME \
      --region $AWS_REGION \
      --query 'nodegroups[0]' \
      --output text 2>/dev/null || echo "")

    if [ -n "$NODEGROUP" ]; then
      DESIRED_SIZE=$(aws eks describe-nodegroup \
        --cluster-name $CLUSTER_NAME \
        --nodegroup-name $NODEGROUP \
        --region $AWS_REGION \
        --query 'nodegroup.scalingConfig.desiredSize' \
        --output text 2>/dev/null || echo "0")

      if [ "$DESIRED_SIZE" == "0" ]; then
        echo -e "${YELLOW}⚠️  Nodes are stopped. Starting...${NC}"
        cd $PROJECT_ROOT/deploy/kubernetes/scripts
        ./start-cluster.sh
      else
        echo -e "${GREEN}✅ Nodes are already running ($DESIRED_SIZE nodes)${NC}"
      fi
    fi
  fi
else
  echo -e "${RED}❌ Stack is in unexpected state: $STACK_STATUS${NC}"
  echo "Please check AWS Console or run: aws cloudformation describe-stacks --stack-name $STACK_NAME"
  exit 1
fi

# Step 2: Configure kubectl
echo ""
echo -e "${YELLOW}📦 Step 2: Configuring kubectl...${NC}"
CLUSTER_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
  --output text)

aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
echo -e "${GREEN}✅ kubectl configured${NC}"

# Verify cluster access
kubectl get nodes > /dev/null 2>&1 || {
  echo -e "${RED}❌ Cannot access cluster. Waiting for nodes...${NC}"
  sleep 30
}

# Step 3: Check if ALB Controller is installed
echo ""
echo -e "${YELLOW}📦 Step 3: Checking AWS Load Balancer Controller...${NC}"
if kubectl get deployment aws-load-balancer-controller -n kube-system > /dev/null 2>&1; then
  echo -e "${GREEN}✅ ALB Controller already installed${NC}"
else
  echo -e "${YELLOW}⚠️  Installing ALB Controller...${NC}"
  cd $PROJECT_ROOT/deploy/kubernetes/scripts
  ./install-alb-controller.sh
fi

# Step 4: Build and push Docker image
echo ""
echo -e "${YELLOW}📦 Step 4: Docker image...${NC}"
ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
  --output text)

echo "ECR Repository: $ECR_REPO"

# Check if image exists
IMAGE_EXISTS=$(aws ecr describe-images \
  --repository-name $(echo $ECR_REPO | cut -d'/' -f2) \
  --image-ids imageTag=latest \
  --region $AWS_REGION \
  --query 'imageDetails[0].imageTags[0]' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$IMAGE_EXISTS" == "NOT_FOUND" ]; then
  echo -e "${YELLOW}⚠️  Image not found. Building and pushing...${NC}"

  # Login to ECR
  aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $(echo $ECR_REPO | cut -d'/' -f1)

  # Build image
  cd $PROJECT_ROOT
  docker build -t $ECR_REPO:latest -f deploy/docker/api/Dockerfile .

  # Push image
  docker push $ECR_REPO:latest
  echo -e "${GREEN}✅ Image built and pushed${NC}"
else
  echo -e "${GREEN}✅ Image already exists: $IMAGE_EXISTS${NC}"
  if [ "$AUTO_CONFIRM" == "yes" ]; then
    echo -e "${GREEN}✅ AUTO_CONFIRM=yes, skipping rebuild${NC}"
  else
    echo -e "${YELLOW}Rebuild? (y/N)${NC}"
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $(echo $ECR_REPO | cut -d'/' -f1)
      cd $PROJECT_ROOT
      docker build -t $ECR_REPO:latest -f deploy/docker/api/Dockerfile .
      docker push $ECR_REPO:latest
      echo -e "${GREEN}✅ Image rebuilt and pushed${NC}"
    fi
  fi
fi

# Step 5: Deploy Kubernetes applications
echo ""
echo -e "${YELLOW}📦 Step 5: Deploying Kubernetes applications...${NC}"

# Check if namespace exists
if kubectl get namespace prod > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Namespace 'prod' already exists${NC}"
  if [ "$AUTO_CONFIRM" == "yes" ]; then
    echo -e "${GREEN}✅ AUTO_CONFIRM=yes, redeploying applications${NC}"
    cd $PROJECT_ROOT/deploy/kubernetes

    # Update image in deployment
    sed -i.bak "s|PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest|$ECR_REPO:latest|g" base/api/deployment.yaml

    # Apply configurations
    ./scripts/deploy.sh
  else
    echo -e "${YELLOW}Redeploy applications? (y/N)${NC}"
    read -p "" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Skipping deployment."
    else
      cd $PROJECT_ROOT/deploy/kubernetes

      # Update image in deployment
      sed -i.bak "s|PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest|$ECR_REPO:latest|g" base/api/deployment.yaml

      # Apply configurations
      ./scripts/deploy.sh
    fi
  fi
else
  echo -e "${YELLOW}⚠️  Deploying for the first time...${NC}"
  cd $PROJECT_ROOT/deploy/kubernetes

  # Update image in deployment
  sed -i.bak "s|PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest|$ECR_REPO:latest|g" base/api/deployment.yaml

  # Apply configurations
  ./scripts/deploy.sh
fi

# Step 6: Wait for pods to be ready
echo ""
echo -e "${YELLOW}📦 Step 6: Waiting for all pods to be ready...${NC}"
kubectl wait --for=condition=Ready pods --all -n prod --timeout=300s || {
  echo -e "${YELLOW}⚠️  Some pods may not be ready yet. Check with: kubectl get pods -n prod${NC}"
}

# Step 7: Get access URLs
echo ""
echo -e "${YELLOW}📦 Step 7: Getting access URLs...${NC}"
echo "Waiting for ALB to be provisioned (this may take 2-3 minutes)..."

ALB_URL=""
for i in {1..30}; do
  ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
  if [ -n "$ALB_URL" ]; then
    break
  fi
  echo "Attempt $i/30..."
  sleep 10
done

# Final summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All services are running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -n "$ALB_URL" ]; then
  echo "🌐 Access your application:"
  echo "   Main App:    http://$ALB_URL"
  echo "   API Docs:    http://$ALB_URL/docs"
  echo "   Phoenix:     http://$ALB_URL/phoenix"
  echo "   Langfuse:    http://$ALB_URL/langfuse"
else
  echo "⚠️  ALB URL not available yet. Check later with:"
  echo "   kubectl get ingress -n prod"
fi

echo ""
echo "📊 Check status:"
echo "   kubectl get pods -n prod"
echo "   kubectl get services -n prod"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop-all.sh"
