# Sandbox function declaration (lives in the private subnets behind a security group without rules, see SandboxLambda)
# One command per invocation over a copy of the run's workspace, every invocation in a microVM of its own
resource "aws_lambda_function" "sandbox" {
  function_name = local.sandbox_name
  role          = aws_iam_role.sandbox.arn
  package_type  = "Image"
  image_uri     = var.sandbox_image
  architectures = ["arm64"]
  memory_size   = var.sandbox_memory_size
  timeout       = var.sandbox_timeout

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.sandbox.id]
  }

  depends_on = [aws_cloudwatch_log_group.sandbox, aws_iam_role_policy_attachment.sandbox_vpc_access]

  #checkov:skip=CKV_AWS_50:Tracing would add an X-Ray daemon call to a function that must reach nothing
  #checkov:skip=CKV_AWS_116:The server invokes it synchronously and gets every failure back, there is nothing to dead-letter
  #checkov:skip=CKV_AWS_115:The server leases at most 10 commands at once, reserved concurrency needs an account limit above 100
  #checkov:skip=CKV_AWS_272:The function is an image pinned by digest, code signing applies to zip packages
  #checkov:skip=CKV_AWS_173:The function has no environment variables
}

# Log group declaration (what the sandbox function prints, kept for log_retention_days)
resource "aws_cloudwatch_log_group" "sandbox" {
  name              = "/aws/lambda/${local.sandbox_name}"
  retention_in_days = var.log_retention_days

  #checkov:skip=CKV_AWS_158:The logs are encrypted by CloudWatch, a customer managed KMS key is not worth its price here
  #checkov:skip=CKV_AWS_338:Logs are kept for log_retention_days, a year of them is not needed
}

# The sandbox function runs code a model wrote, its security group has no rule, so nothing reaches it and it reaches nothing
# An empty egress list removes the allow-all rule AWS adds to every new security group
resource "aws_security_group" "sandbox" {
  name        = local.sandbox_name
  description = "Security group of the sandbox function, no traffic in or out"
  vpc_id      = var.vpc_id
  egress      = []

  tags = {
    Name = local.sandbox_name
  }
}

# IAM role declaration for the sandbox function
# It may only write its logs and attach to the VPC, so code it runs has no permission to call anything in AWS
data "aws_iam_policy_document" "sandbox_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sandbox" {
  name                 = local.sandbox_name
  assume_role_policy   = data.aws_iam_policy_document.sandbox_assume_role.json
  permissions_boundary = var.permissions_boundary_arn
}

resource "aws_iam_role_policy_attachment" "sandbox_vpc_access" {
  role       = aws_iam_role.sandbox.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
