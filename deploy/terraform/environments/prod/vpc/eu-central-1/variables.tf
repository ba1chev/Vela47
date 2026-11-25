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
    environment = "production"
    created_by  = "terraform"
  }
}

variable "name" {
  description = "Name of the VPC, also the prefix of the Name tag of everything in it"
  type        = string
  default     = "vela47"
}

variable "cidr_block" {
  description = "CIDR of the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr_blocks" {
  description = "CIDRs of the public subnets (load balancer and NAT gateway), one subnet per availability zone"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidr_blocks" {
  description = "CIDRs of the private subnets (EC2 instance, server task, sandbox function and database), one subnet per availability zone"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}
