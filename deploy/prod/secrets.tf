# Application secret declaration (token signing key, the admin bootstrapped on the first start and the web search key)
# The server reads it once at startup, VELA47_APP_SECRET_ID points to it
resource "random_password" "token_secret" {
  length  = var.app_token_secret_length
  special = false
}

resource "random_password" "admin_password" {
  length  = var.app_admin_password_length
  special = false
}

resource "aws_secretsmanager_secret" "app" {
  name                    = var.app_secret_name
  recovery_window_in_days = var.app_secret_recovery_window_in_days
  tags                    = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    token_secret   = random_password.token_secret.result
    admin_username = var.app_admin_username
    admin_password = random_password.admin_password.result
    tavily_api_key = var.app_tavily_api_key
  })
}
