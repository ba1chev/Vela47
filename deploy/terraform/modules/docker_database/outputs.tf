output "container_address" {
  description = "Address of the database container on its network"
  value       = docker_container.this.network_data[0].ip_address
}

output "password" {
  description = "Password of the vela47 user on PostgreSQL"
  value       = random_password.this.result
  sensitive   = true
}
