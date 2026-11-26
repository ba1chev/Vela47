variable "region" {
  description = "AWS region where all resources are created"
  type        = string
  default     = "eu-central-1"
}

variable "tags" {
  description = "Tags every resource of the root module gets through default_tags of the provider"
  type        = map(string)
  default = {
    owner       = "ba1chev"
    project     = "vela47"
    environment = "dev"
    created_by  = "terraform"
  }
}

variable "name" {
  description = "Name of the VPC, also the prefix of the Name tag of everything in it"
  type        = string
  default     = "vela47-dev"
}

variable "cidr_block" {
  description = "CIDR of the VPC, a range of its own per environment"
  type        = string
  default     = "10.10.0.0/16"
}

variable "public_subnet_cidr_blocks" {
  description = "CIDRs of the public subnets (load balancer and NAT), one subnet per availability zone"
  type        = list(string)
  default     = ["10.10.1.0/24", "10.10.2.0/24"]
}

variable "private_subnet_cidr_blocks" {
  description = "CIDRs of the private subnets (EC2 instances, server tasks, sandbox function and database), one subnet per availability zone"
  type        = list(string)
  default     = ["10.10.11.0/24", "10.10.12.0/24"]
}

variable "nat_type" {
  description = "How the private subnets reach the internet, a NAT gateway or a NAT instance"
  type        = string
  default     = "instance"
}
