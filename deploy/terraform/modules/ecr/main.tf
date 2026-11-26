# ECR repository declarations, one per image of a release, shared by every AWS environment
# A release is built once and its images are promoted from dev to staging and prod by digest, so tags never move
resource "aws_ecr_repository" "this" {
  for_each = toset(var.repositories)

  name                 = "${var.name}-${each.value}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  #checkov:skip=CKV_AWS_136:AES256 avoids the price of a customer managed KMS key, the images hold no secrets
}

# Untagged images go after a day, and only the newest tagged ones are kept, enough for every environment and a rollback
resource "aws_ecr_lifecycle_policy" "this" {
  for_each = aws_ecr_repository.this

  repository = each.value.name
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Remove untagged images"
        selection    = { tagStatus = "untagged", countType = "sinceImagePushed", countUnit = "days", countNumber = 1 }
        action       = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep the newest releases"
        selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = var.kept_images }
        action       = { type = "expire" }
      },
    ]
  })
}

# Lambda pulls the sandbox image with its own service principal, only for functions of this project
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_iam_policy_document" "lambda_pull" {
  statement {
    sid     = "LambdaPull"
    actions = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "aws:sourceArn"
      values   = ["arn:aws:lambda:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:function:${var.name}-*"]
    }
  }
}

resource "aws_ecr_repository_policy" "lambda_pull" {
  for_each = toset(var.lambda_repositories)

  repository = aws_ecr_repository.this[each.value].name
  policy     = data.aws_iam_policy_document.lambda_pull.json
}
