output "url" {
  description = "Where the UI is served, through the load balancer."
  value       = "${lower(var.load_balancer_listener_protocol)}://${aws_lb.load_balancer.dns_name}:${var.load_balancer_listener_port}"
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
  description = "The auto scaling group that runs the EC2 instances."
  value       = aws_autoscaling_group.web.name
}

output "target_group_arn" {
  description = "Target group of the EC2 instances. Check their health with `aws elbv2 describe-target-health --target-group-arn <arn>`."
  value       = aws_lb_target_group.web.arn
}
