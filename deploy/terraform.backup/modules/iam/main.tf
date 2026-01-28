# IAM Module for KnowledgeWeaver
# Creates IAM roles and policies for EKS pods

locals {
  name = "${var.project_name}-${var.environment}"
}

# Pod Execution Role (IRSA - IAM Roles for Service Accounts)
# This role allows pods to access AWS services

# S3 Access Policy for application pods
resource "aws_iam_policy" "pod_s3_access" {
  name        = "${local.name}-pod-s3-access"
  description = "Allow pods to access S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })
}

# CloudWatch Logs Access Policy
resource "aws_iam_policy" "pod_cloudwatch_logs" {
  name        = "${local.name}-pod-cloudwatch-logs"
  description = "Allow pods to write to CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/eks/${var.cluster_name}/*"
      }
    ]
  })
}

# Pod Execution Role
resource "aws_iam_role" "pod_execution" {
  name = "${local.name}-pod-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Condition = {
        StringEquals = {
          "${replace(var.oidc_provider_arn, "/^(.*provider/)/", "")}:sub" = "system:serviceaccount:prod:knowledgeweaver-sa"
          "${replace(var.oidc_provider_arn, "/^(.*provider/)/", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = {
    Name = "${local.name}-pod-execution-role"
  }
}

# Attach policies to pod execution role
resource "aws_iam_role_policy_attachment" "pod_s3_access" {
  policy_arn = aws_iam_policy.pod_s3_access.arn
  role       = aws_iam_role.pod_execution.name
}

resource "aws_iam_role_policy_attachment" "pod_cloudwatch_logs" {
  policy_arn = aws_iam_policy.pod_cloudwatch_logs.arn
  role       = aws_iam_role.pod_execution.name
}
