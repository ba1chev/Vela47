# ECR repository declarations (the server image and the sandbox function image)
# force_delete lets terraform destroy remove a repository that still holds images
resource "aws_ecr_repository" "app" {
  name                 = var.app_repository_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
  tags                 = local.common_tags
}

resource "aws_ecr_repository" "sandbox" {
  name                 = var.sandbox_repository_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
  tags                 = local.common_tags
}

# Only the newest images are kept, the older ones are deleted
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the newest images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = var.ecr_kept_images }
      action       = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "sandbox" {
  repository = aws_ecr_repository.sandbox.name
  policy     = aws_ecr_lifecycle_policy.app.policy
}

# Image declarations (built here for arm64, the Graviton instance and the Lambda function both run on it, then pushed)
# Without provenance and SBOM attestations BuildKit writes a single image manifest instead of an index around it,
# the only form Lambda accepts
resource "docker_image" "app" {
  name = "${aws_ecr_repository.app.repository_url}:${local.app_image_tag}"

  build {
    context    = local.repository
    dockerfile = local.app_dockerfile
    platform   = "linux/arm64"
    provenance = "false"
    sbom       = "false"
  }
}

resource "docker_registry_image" "app" {
  name          = docker_image.app.name
  keep_remotely = true
}

resource "docker_image" "sandbox" {
  name = "${aws_ecr_repository.sandbox.repository_url}:${local.sandbox_image_tag}"

  build {
    context    = local.sandbox_context
    platform   = "linux/arm64"
    provenance = "false"
    sbom       = "false"
  }
}

resource "docker_registry_image" "sandbox" {
  name          = docker_image.sandbox.name
  keep_remotely = true
}
