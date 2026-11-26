output "url" {
  description = "Where the UI is served"
  value       = module.docker_app.url
}

output "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  value       = module.docker_app.admin_username
}

output "admin_password" {
  description = "Password of the admin bootstrapped on the first start. Read it with `terraform output -raw admin_password`"
  value       = module.docker_app.admin_password
  sensitive   = true
}

output "database_password" {
  description = "Password of the vela47 user on the published PostgreSQL"
  value       = module.docker_database.password
  sensitive   = true
}
