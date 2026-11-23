# Log group declarations (what the server task and the sandbox function print, kept for log_retention_days)
resource "aws_cloudwatch_log_group" "app" {
  name              = var.app_log_group_name
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "sandbox" {
  name              = "/aws/lambda/${var.sandbox_function_name}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}
