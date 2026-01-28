# Variables for KnowledgeWeaver Infrastructure

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"  # Sydney (closest to NZ)
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "knowledgeweaver"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "owner" {
  description = "Owner/maintainer of the infrastructure"
  type        = string
  default     = "sheldon"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b"]
}

# EKS Configuration
variable "eks_cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_group_config" {
  description = "EKS node group configuration"
  type = object({
    instance_types = list(string)
    disk_size      = number
    min_size       = number
    max_size       = number
    desired_size   = number
  })
  default = {
    instance_types = ["t3.medium"]
    disk_size      = 50
    min_size       = 0  # Can scale to 0 to save cost
    max_size       = 5
    desired_size   = 2  # Start with 2 nodes
  }
}

# ECR Configuration
variable "ecr_repositories" {
  description = "List of ECR repositories to create"
  type        = list(string)
  default     = ["knowledgeweaver-api"]
}

# S3 Configuration
variable "s3_bucket_name" {
  description = "S3 bucket name for document storage"
  type        = string
  default     = ""  # Will be generated if not provided
}

# CloudWatch Configuration
variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

# Cost Control
variable "enable_nat_gateway" {
  description = "Enable NAT gateway (costs $32-64/month, disable for cost savings)"
  type        = bool
  default     = true
}
