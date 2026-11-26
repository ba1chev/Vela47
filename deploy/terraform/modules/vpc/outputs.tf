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

output "eip_nat_public_ip" {
  description = "Public address the private subnets reach the internet from, through the NAT gateway or the NAT instance"
  value       = aws_eip.this.public_ip
}

output "cidr_block" {
  description = "CIDR of the VPC"
  value       = aws_vpc.this.cidr_block
}
