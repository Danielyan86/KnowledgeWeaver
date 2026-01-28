# Outputs for KnowledgeWeaver Infrastructure

# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

# EKS Outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# ECR Outputs
output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value       = module.ecr.repository_urls
}

# S3 Outputs
output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3.bucket_arn
}

# IAM Outputs
output "eks_node_role_arn" {
  description = "EKS node IAM role ARN"
  value       = module.iam.eks_node_role_arn
}

output "pod_execution_role_arn" {
  description = "Pod execution IAM role ARN"
  value       = module.iam.pod_execution_role_arn
}

# Quick Start Commands
output "quick_start_commands" {
  description = "Quick start commands"
  value = <<-EOT
    # 1. Configure kubectl
    ${module.eks.configure_kubectl_command}

    # 2. Verify cluster
    kubectl get nodes

    # 3. Deploy application
    cd ../kubernetes/scripts
    ./deploy.sh

    # 4. Get application URL (after ALB is provisioned)
    kubectl get ingress -n prod

    # 5. Stop cluster (when done)
    ./stop-cluster.sh
  EOT
}
