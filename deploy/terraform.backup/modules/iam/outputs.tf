output "pod_execution_role_arn" {
  description = "Pod execution IAM role ARN"
  value       = aws_iam_role.pod_execution.arn
}

output "pod_execution_role_name" {
  description = "Pod execution IAM role name"
  value       = aws_iam_role.pod_execution.name
}

output "eks_node_role_arn" {
  description = "EKS node IAM role ARN (from EKS module)"
  value       = ""  # This is handled by EKS module
}
