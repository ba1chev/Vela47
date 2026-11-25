# Application secret declaration (token signing key, the admin bootstrapped on the first start and the web search key)
# The server reads it once at startup, VELA47_APP_SECRET_ID points to it
resource "random_password" "token_secret" {
  length  = var.token_secret_length
  special = false
}

resource "random_password" "admin_password" {
  length  = var.admin_password_length
  special = false
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${var.name}/app"
  recovery_window_in_days = var.secret_recovery_window_in_days
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    token_secret   = random_password.token_secret.result
    admin_username = var.admin_username
    admin_password = random_password.admin_password.result
    tavily_api_key = var.tavily_api_key
  })
}
