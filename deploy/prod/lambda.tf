# Sandbox function declaration (lives in the private subnets behind a security group without rules, see SandboxLambda)
# One command per invocation over a copy of the run's workspace, every invocation in a microVM of its own
resource "aws_lambda_function" "sandbox" {
  function_name = var.sandbox_function_name
  role          = aws_iam_role.sandbox.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.sandbox.repository_url}@${docker_registry_image.sandbox.sha256_digest}"
  architectures = ["arm64"]
  memory_size   = var.sandbox_memory_size
  timeout       = var.sandbox_timeout
  tags          = local.common_tags

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.sandbox.id]
  }

  depends_on = [aws_cloudwatch_log_group.sandbox, aws_iam_role_policy_attachment.sandbox_vpc_access]
}
