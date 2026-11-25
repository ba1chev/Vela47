output "url" {
  description = "Where the UI is served, over HTTPS through the load balancer"
  value       = "https://${module.app.route53_record_fqdn}"
}

output "lb_dns_name" {
  description = "DNS name of the load balancer, the target of the alias record of the application domain"
  value       = module.app.lb_dns_name
}

output "lb_target_group_arn" {
  description = "ARN of the target group of the server tasks. Check their health with `aws elbv2 describe-target-health --target-group-arn <arn>`"
  value       = module.app.lb_target_group_arn
}

output "autoscaling_group_name" {
  description = "Name of the auto scaling group which runs the EC2 instance of the cluster"
  value       = module.app.autoscaling_group_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster. A code change is deployed by terraform apply, which builds and pushes a new image and updates the service"
  value       = module.app.ecs_cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service of the server task. Follow a deploy with `aws ecs describe-services --cluster <cluster> --services <service>`"
  value       = module.app.ecs_service_name
}

output "ecr_image_app_uri" {
  description = "URI of the server image the task runs, pinned by digest"
  value       = module.app.ecr_image_app_uri
}

output "cloudwatch_log_group_app_name" {
  description = "Name of the log group of the server task. Follow it with `aws logs tail <name> --follow`"
  value       = module.app.cloudwatch_log_group_app_name
}

output "lambda_function_name" {
  description = "Name of the Lambda function the TEST subagent runs its commands in"
  value       = module.app.lambda_function_name
}

output "secretsmanager_secret_app_arn" {
  description = "ARN of the application secret with the token signing key and the bootstrapped admin, VELA47_APP_SECRET_ID"
  value       = module.app.secretsmanager_secret_app_arn
}

output "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  value       = module.app.admin_username
}

output "admin_password" {
  description = "Password of the admin bootstrapped on the first start. Read it with `terraform output -raw admin_password`"
  value       = module.app.admin_password
  sensitive   = true
}
