output "log_group_names" {
  description = "CloudWatch log group names"
  value = {
    cluster     = aws_cloudwatch_log_group.eks_cluster.name
    application = aws_cloudwatch_log_group.application.name
  }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  value       = aws_sns_topic.alarms.arn
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
