# Paths of the images, and the files whose change rebuilds each of them
# An image is tagged with a hash of its files, so a change gives a new tag and ECS deploys it
locals {
  sandbox_context = "${var.repository_path}/${var.sandbox_context}"
  app_source_files = sort([
    for current_file in setunion(
      fileset(var.repository_path, "app/**"),
      fileset(var.repository_path, "db/**"),
      ["requirements.txt", var.app_dockerfile]
    ) : current_file if !strcontains(current_file, "__pycache__") && !strcontains(current_file, ".sqlite3")
  ])
  app_image_tag = substr(sha1(join("", [
    for current_file in local.app_source_files : filesha1("${var.repository_path}/${current_file}")
  ])), 0, 12)
  sandbox_image_tag = substr(sha1(join("", [
    for current_file in sort(fileset(local.sandbox_context, "*")) : filesha1("${local.sandbox_context}/${current_file}")
  ])), 0, 12)
  app_image     = "${aws_ecr_repository.app.repository_url}@${docker_registry_image.app.sha256_digest}"
  sandbox_image = "${aws_ecr_repository.sandbox.repository_url}@${docker_registry_image.sandbox.sha256_digest}"
}

# ECR repository declarations (the server image and the sandbox function image)
# force_delete lets terraform destroy remove a repository that still holds images
resource "aws_ecr_repository" "app" {
  name                 = local.app_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

resource "aws_ecr_repository" "sandbox" {
  name                 = local.sandbox_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
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
    context    = var.repository_path
    dockerfile = var.app_dockerfile
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
