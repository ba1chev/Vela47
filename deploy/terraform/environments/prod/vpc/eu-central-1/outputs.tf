output "vpc_id" {
  description = "ID of the VPC every resource of the environment lives in"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets of the load balancer and the NAT gateway"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets of the EC2 instance, the server task, the sandbox function and the database"
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_public_ip" {
  description = "Public address the server task reaches Bedrock and the web from"
  value       = module.vpc.nat_gateway_public_ip
}
