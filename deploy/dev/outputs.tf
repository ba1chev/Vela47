output "url" {
  description = "Where the UI is served."
  value       = "http://127.0.0.1:8000"
}

output "admin_username" {
  description = "The admin bootstrapped on the first start."
  value       = local.admin_username
}

output "admin_password" {
  description = "Password of that admin. Read it with `terraform output -raw admin_password`."
  value       = random_password.admin_password.result
  sensitive   = true
}

output "database_password" {
  description = "Password of the vela47 user on the PostgreSQL published at 127.0.0.1:5432."
  value       = random_password.database_password.result
  sensitive   = true
}
