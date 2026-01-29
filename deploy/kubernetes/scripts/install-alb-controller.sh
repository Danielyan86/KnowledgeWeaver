#!/bin/bash
# Install AWS Load Balancer Controller for EKS

set -e

echo "=== Installing AWS Load Balancer Controller ==="

# Variables
CLUSTER_NAME="knowledgeweaver-production"
REGION="ap-southeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. Create IAM OIDC provider (if not exists)
echo "1. Checking OIDC provider..."
eksctl utils associate-iam-oidc-provider \
    --cluster ${CLUSTER_NAME} \
    --region ${REGION} \
    --approve || echo "OIDC provider already exists"

# 2. Create IAM policy for ALB controller
echo "2. Creating IAM policy..."
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam-policy.json || echo "Policy already exists"

# 3. Create service account with IAM role
echo "3. Creating service account..."
eksctl create iamserviceaccount \
    --cluster=${CLUSTER_NAME} \
    --region=${REGION} \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
    --override-existing-serviceaccounts \
    --approve

# 4. Install cert-manager (required by ALB controller)
echo "4. Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

echo "Waiting for cert-manager to be ready..."
kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager -n cert-manager
kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager-webhook -n cert-manager

# 5. Install AWS Load Balancer Controller using Helm
echo "5. Installing AWS Load Balancer Controller..."
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=${CLUSTER_NAME} \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller \
    --set region=${REGION} \
    --set vpcId=$(aws eks describe-cluster --name ${CLUSTER_NAME} --region ${REGION} --query "cluster.resourcesVpcConfig.vpcId" --output text)

echo ""
echo "=== Waiting for ALB controller to be ready... ==="
kubectl wait --for=condition=Available --timeout=300s deployment/aws-load-balancer-controller -n kube-system

echo ""
echo "✅ AWS Load Balancer Controller installed successfully!"
echo ""
echo "Next steps:"
echo "1. Apply your Ingress: kubectl apply -f deploy/kubernetes/base/ingress.yaml"
echo "2. Get ALB URL: kubectl get ingress -n demo"
echo ""

rm -f iam-policy.json
