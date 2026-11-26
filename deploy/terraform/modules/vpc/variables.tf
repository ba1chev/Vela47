variable "name" {
  description = "Name of the VPC, also the prefix of the Name tag of everything in it"
  type        = string
}

variable "cidr_block" {
  description = "CIDR of the VPC"
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "The cidr_block must be a valid IPv4 CIDR, e.g. 10.0.0.0/16."
  }
}

variable "public_subnet_cidr_blocks" {
  description = "CIDRs of the public subnets, one subnet per availability zone"
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_cidr_blocks) >= 2
    error_message = "A load balancer needs at least 2 public subnets in different availability zones."
  }
}

variable "private_subnet_cidr_blocks" {
  description = "CIDRs of the private subnets, one subnet per availability zone"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_cidr_blocks) >= 2
    error_message = "An RDS subnet group needs at least 2 private subnets in different availability zones."
  }
}

variable "nat_type" {
  description = "How the private subnets reach the internet: a managed NAT gateway, or a NAT instance at a tenth of the price"
  type        = string
  default     = "gateway"

  validation {
    condition     = contains(["gateway", "instance"], var.nat_type)
    error_message = "The nat_type must be gateway or instance."
  }
}

variable "nat_instance_type" {
  description = "Instance type of the NAT instance, an arm64 type since the AMI is the arm64 Amazon Linux 2023"
  type        = string
  default     = "t4g.nano"
}
