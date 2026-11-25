output "db_instance_address" {
  description = "Host name of the RDS instance, VELA47_DATABASE_HOST. It follows the primary through a failover"
  value       = module.database.db_instance_address
}

output "db_instance_port" {
  description = "Port of the RDS instance, VELA47_DATABASE_PORT"
  value       = module.database.db_instance_port
}

output "db_instance_name" {
  description = "Database on the RDS instance, VELA47_DATABASE_NAME"
  value       = module.database.db_instance_name
}

output "db_instance_master_user_secret_arn" {
  description = "ARN of the RDS-managed secret with the database username and password, VELA47_DATABASE_SECRET_ID"
  value       = module.database.db_instance_master_user_secret_arn
}

output "security_group_id" {
  description = "ID of the security group of the RDS instance, the app root module adds its ingress rule to it"
  value       = module.database.security_group_id
}
