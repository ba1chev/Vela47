output "route53_record_fqdn" {
  description = "Domain the application is served on over HTTPS"
  value       = aws_route53_record.app.fqdn
}

output "lb_dns_name" {
  description = "DNS name of the load balancer, the target of the application domain"
  value       = aws_lb.this.dns_name
}

output "lb_target_group_arns" {
  description = "ARNs of the blue and green target groups of the server tasks"
  value       = { for current_name, current in aws_lb_target_group.this : current_name => current.arn }
}

output "autoscaling_group_name" {
  description = "Name of the auto scaling group which runs the EC2 instances of the cluster"
  value       = aws_autoscaling_group.this.name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.this.name
}

output "ecs_service_name" {
  description = "Name of the ECS service of the server tasks"
  value       = aws_ecs_service.this.name
}

output "ecs_service_arn" {
  description = "ARN of the ECS service of the server tasks"
  value       = aws_ecs_service.this.arn
}

output "cloudwatch_log_group_app_name" {
  description = "Name of the log group of the server tasks"
  value       = aws_cloudwatch_log_group.app.name
}

output "lambda_function_name" {
  description = "Name of the Lambda function the TEST subagent runs its commands in"
  value       = aws_lambda_function.sandbox.function_name
}

output "secretsmanager_secret_app_arn" {
  description = "ARN of the application secret with the token signing key and the bootstrapped admin, VELA47_APP_SECRET_ID"
  value       = aws_secretsmanager_secret.app.arn
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
