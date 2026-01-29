#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔐 Creating Kubernetes Secrets from .env file${NC}"
echo ""

# Check if .env file exists
if [ ! -f "../../../.env" ]; then
  echo -e "${RED}❌ Error: .env file not found${NC}"
  echo "Please create .env file in project root first"
  exit 1
fi

# Load .env file
set -a
source ../../../.env
set +a

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
  echo -e "${RED}❌ Error: kubectl not configured${NC}"
  echo "Run: aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production"
  exit 1
fi

# Create namespace if not exists
kubectl create namespace prod --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ Namespace 'prod' ready${NC}"

# Create knowledgeweaver-secrets
echo -e "${YELLOW}Creating knowledgeweaver-secrets...${NC}"
kubectl create secret generic knowledgeweaver-secrets \
  --from-literal=NEO4J_PASSWORD="${NEO4J_PASSWORD}" \
  --from-literal=LLM_BINDING_API_KEY="${LLM_BINDING_API_KEY}" \
  --from-literal=GEMINI_API_KEY="${GEMINI_API_KEY}" \
  --from-literal=LANGFUSE_PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY}" \
  --from-literal=LANGFUSE_SECRET_KEY="${LANGFUSE_SECRET_KEY}" \
  --namespace prod \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ knowledgeweaver-secrets created${NC}"

# Generate random secrets for Langfuse
NEXTAUTH_SECRET=$(openssl rand -base64 32)
SALT=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)

echo -e "${YELLOW}Creating langfuse-secrets...${NC}"
kubectl create secret generic langfuse-secrets \
  --from-literal=NEXTAUTH_SECRET="${NEXTAUTH_SECRET}" \
  --from-literal=SALT="${SALT}" \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  --namespace prod \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ langfuse-secrets created${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All secrets created successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Verify with:"
echo "  kubectl get secrets -n prod"
echo ""
echo "View secret (base64 decoded):"
echo "  kubectl get secret knowledgeweaver-secrets -n prod -o jsonpath='{.data.NEO4J_PASSWORD}' | base64 -d"
echo ""
