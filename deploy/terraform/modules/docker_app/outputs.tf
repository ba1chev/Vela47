output "url" {
  description = "Where the UI is served"
  value       = "http://${var.published_address}:${var.published_port}"
}

output "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  value       = var.admin_username
}

output "admin_password" {
  description = "Password of the admin bootstrapped on the first start"
  value       = random_password.admin_password.result
  sensitive   = true
}
