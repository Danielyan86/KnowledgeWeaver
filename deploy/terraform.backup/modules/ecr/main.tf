# ECR Module for KnowledgeWeaver
# Creates Docker image repositories

locals {
  name = "${var.project_name}-${var.environment}"
}

# ECR Repositories
resource "aws_ecr_repository" "repos" {
  for_each = toset(var.repositories)

  name                 = "${local.name}-${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${local.name}-${each.value}"
  }
}

# Lifecycle Policy - Keep only recent images
resource "aws_ecr_lifecycle_policy" "repos" {
  for_each = toset(var.repositories)

  repository = aws_ecr_repository.repos[each.value].name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}
