# CloudWatch Module for KnowledgeWeaver
# Creates log groups, dashboards, and alarms

locals {
  name = "${var.project_name}-${var.environment}"
}

# CloudWatch Log Group for EKS Cluster
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name}-eks-logs"
  }
}

# CloudWatch Log Group for Application
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/${var.cluster_name}/application"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name}-app-logs"
  }
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name = "${local.name}-alarms"

  tags = {
    Name = "${local.name}-alarms"
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = local.name

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/EKS", "cluster_failed_node_count", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "EKS Failed Nodes"
        }
      },
      {
        type = "log"
        properties = {
          query   = "SOURCE '${aws_cloudwatch_log_group.application.name}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
          region  = data.aws_region.current.name
          title   = "Recent Application Logs"
        }
      }
    ]
  })
}

# Cost Alarm
resource "aws_cloudwatch_metric_alarm" "high_cost" {
  alarm_name          = "${local.name}-high-daily-cost"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400  # 1 day
  statistic           = "Maximum"
  threshold           = 5
  alarm_description   = "Alert when daily AWS cost exceeds $5"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    Currency = "USD"
  }
}

data "aws_region" "current" {}
