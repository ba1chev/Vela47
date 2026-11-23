# Passwords declaration (kept in the Terraform state, read them with terraform output)
resource "random_password" "token_secret" {
  length  = var.app_token_secret_length
  special = false
}

resource "random_password" "admin_password" {
  length  = var.app_admin_password_length
  special = false
}

resource "random_password" "database_password" {
  length  = var.database_password_length
  special = false
}
