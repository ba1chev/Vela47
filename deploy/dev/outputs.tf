output "url" {
  description = "Where the UI is served."
  value       = "http://${var.published_address}:${var.application_published_port}"
}

output "admin_username" {
  description = "The admin bootstrapped on the first start."
  value       = var.app_admin_username
}

output "admin_password" {
  description = "Password of that admin. Read it with `terraform output -raw admin_password`."
  value       = random_password.admin_password.result
  sensitive   = true
}

output "database_password" {
  description = "Password of the vela47 user on the published PostgreSQL."
  value       = random_password.database_password.result
  sensitive   = true
}
