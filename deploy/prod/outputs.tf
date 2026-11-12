output "url" {
  description = "Where the UI is served, over HTTPS through the load balancer."
  value       = "https://${var.app_domain_name}"
}

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer, the target for a CNAME or alias record."
  value       = aws_lb.load_balancer.dns_name
}

output "vpc_id" {
  description = "The VPC every resource lives in."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Subnets of the load balancer and the NAT gateway, one per availability zone."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Subnets of the EC2 instances, one per availability zone."
  value       = aws_subnet.private[*].id
}

output "nat_public_ip" {
  description = "Address the EC2 instances reach the internet from."
  value       = aws_eip.nat.public_ip
}

output "autoscaling_group_name" {
  description = "The auto scaling group that runs the EC2 instance. Deploy what is on the branch now with `aws autoscaling start-instance-refresh --auto-scaling-group-name <name>`."
  value       = aws_autoscaling_group.web.name
}

output "target_group_arn" {
  description = "Target group of the EC2 instances. Check their health with `aws elbv2 describe-target-health --target-group-arn <arn>`."
  value       = aws_lb_target_group.web.arn
}

output "database_address" {
  description = "Host name of the RDS instance, VELA47_DATABASE_HOST. It follows the primary through a failover."
  value       = aws_db_instance.database.address
}

output "database_secret_arn" {
  description = "The RDS-managed secret with the database username and password, VELA47_DATABASE_SECRET_ID."
  value       = aws_db_instance.database.master_user_secret[0].secret_arn
}

output "app_secret_arn" {
  description = "The secret with the token signing key and the bootstrapped admin, VELA47_APP_SECRET_ID."
  value       = aws_secretsmanager_secret.app.arn
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
