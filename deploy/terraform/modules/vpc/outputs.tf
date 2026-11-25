output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets, one per availability zone"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets, one per availability zone"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_public_ip" {
  description = "Public address the private subnets reach the internet from"
  value       = aws_nat_gateway.this.public_ip
}
