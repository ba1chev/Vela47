output "db_instance_address" {
  description = "Host name of the RDS instance, it follows the primary through a failover"
  value       = aws_db_instance.this.address
}

output "db_instance_port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.this.port
}

output "db_instance_name" {
  description = "Database created on the RDS instance"
  value       = aws_db_instance.this.db_name
}

output "db_instance_master_user_secret_arn" {
  description = "ARN of the RDS-managed secret with the username and password of the master user"
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}

output "security_group_id" {
  description = "ID of the security group of the RDS instance, clients add their ingress rules to it"
  value       = aws_security_group.this.id
}
