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
  description = "Subnets of the EC2 instance, the server task, the sandbox function and the database, one per availability zone."
  value       = aws_subnet.private[*].id
}

output "nat_public_ip" {
  description = "Address the server task reaches Bedrock and the web from."
  value       = aws_eip.nat.public_ip
}

output "autoscaling_group_name" {
  description = "The auto scaling group that runs the EC2 instance of the cluster."
  value       = aws_autoscaling_group.web.name
}

output "ecs_cluster_name" {
  description = "The ECS cluster. A code change is deployed by terraform apply, which builds and pushes a new image and updates the service."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "The ECS service of the server task. Follow a deploy with `aws ecs describe-services --cluster <cluster> --services <service>`."
  value       = aws_ecs_service.app.name
}

output "app_image" {
  description = "The server image the task runs, pinned by digest."
  value       = "${aws_ecr_repository.app.repository_url}@${docker_registry_image.app.sha256_digest}"
}

output "app_log_group_name" {
  description = "Logs of the server task. Follow them with `aws logs tail <name> --follow`."
  value       = aws_cloudwatch_log_group.app.name
}

output "sandbox_function_name" {
  description = "The Lambda function the TEST subagent runs its commands in."
  value       = aws_lambda_function.sandbox.function_name
}

output "target_group_arn" {
  description = "Target group of the server tasks. Check their health with `aws elbv2 describe-target-health --target-group-arn <arn>`."
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
