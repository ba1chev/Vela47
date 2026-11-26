output "vpc_id" {
  description = "ID of the VPC every resource of the environment lives in"
  value       = module.vpc.vpc_id
}

output "cidr_block" {
  description = "CIDR of the VPC"
  value       = module.vpc.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets of the load balancer and the NAT"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets of the EC2 instances, the server tasks, the sandbox function and the database"
  value       = module.vpc.private_subnet_ids
}

output "eip_nat_public_ip" {
  description = "Public address the server tasks reach Bedrock and the web from"
  value       = module.vpc.eip_nat_public_ip
}
