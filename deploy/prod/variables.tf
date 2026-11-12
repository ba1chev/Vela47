# General variables
variable "aws_region" {
  type        = string
  default     = "eu-central-1"
  description = "AWS region where all resources are created"
}

variable "resource_name_tag" {
  type        = string
  default     = "version-1"
  description = "Value of the Name tag for the tagged resources"
}

variable "environment_tag" {
  type        = string
  default     = "production"
  description = "Value of the Environment tag for the tagged resources"
}

# VPC variables
variable "vpc_cidr_block" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR for the VPC"

  validation {
    condition     = can(cidrhost(var.vpc_cidr_block, 0))
    error_message = "The vpc_cidr_block must be a valid IPv4 CIDR, e.g. 10.0.0.0/16."
  }
}

variable "public_subnet_cidr_blocks" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDRs for the public subnets (one subnet per availability zone)"

  validation {
    condition     = length(var.public_subnet_cidr_blocks) >= 2
    error_message = "The ALB needs at least 2 public subnets in different availability zones."
  }
}

variable "private_subnet_cidr_blocks" {
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
  description = "CIDRs for the private subnets (one subnet per availability zone)"
}

# EC2 instance variables
variable "ec2_instance_ami" {
  type        = string
  default     = "resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
  description = "EC2 instance AMI value"
}

variable "ec2_instance_type" {
  type        = string
  default     = "t2.micro"
  description = "EC2 instance type value"
}

variable "ec2_instance_http_port" {
  type        = number
  default     = 80
  description = "Port on which the application on the EC2 instances listens"
}

variable "ec2_instance_egress_cidr_ipv4" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR for IPv4 for outbound traffic for the EC2 instance"
}

variable "ec2_instance_egress_ip_protocol" {
  type        = string
  default     = "-1"
  description = "IP protocol for the outbound traffic of the EC2 instance (-1 means all)"
}

variable "ec2_security_group_name" {
  type        = string
  default     = "ec2-server-instance-sg"
  description = "Name for the security group of the EC2 instance"
}

# Launch template and auto scaling group variables
variable "ec2_launch_template_name" {
  type        = string
  default     = "vela47-launch-template"
  description = "Name for the EC2 instances launch template"
}

variable "ec2_launch_template_min_instances" {
  type        = number
  default     = 2
  description = "Minimum number of EC2 instances running"

  validation {
    condition     = var.ec2_launch_template_min_instances >= 0
    error_message = "The minimum number of instances can not be negative."
  }
}

variable "ec2_launch_template_max_instances" {
  type        = number
  default     = 4
  description = "Maximum number of EC2 instances running"
}

variable "ec2_launch_template_desired_instances" {
  type        = number
  default     = 2
  description = "Desired number of EC2 instances running"
}

variable "ec2_autoscaling_health_check_type" {
  type        = string
  default     = "ELB"
  description = "Health check type of the auto scaling group (EC2 or ELB)"

  validation {
    condition     = contains(["EC2", "ELB"], var.ec2_autoscaling_health_check_type)
    error_message = "The health check type must be EC2 or ELB."
  }
}

# Load balancer variables
variable "load_balancer_name" {
  type        = string
  default     = "vela47-load-balancer"
  description = "Name for the load balancer"
}

variable "load_balancer_type" {
  type        = string
  default     = "application"
  description = "Load balancer type"

  validation {
    condition     = contains(["application", "network", "gateway"], var.load_balancer_type)
    error_message = "The load balancer type must be application, network or gateway."
  }
}

variable "load_balancer_internal" {
  type        = bool
  default     = false
  description = "Whether the load balancer is internal (true) or internet-facing (false)"
}

variable "load_balancer_deletion_protection" {
  type        = bool
  default     = false
  description = "Protects the load balancer from deletion (set to true for real production)"
}

variable "elb_security_group_name" {
  type        = string
  default     = "alb-secuity-group"
  description = "Name for the security group of the ELB instance"
}

variable "load_balancer_ingress_cidr_ipv4" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR for IPv4 for inbound traffic to the load balancer"
}

variable "load_balancer_egress_cidr_ipv4" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR for IPv4 for outbound traffic of the load balancer"
}

variable "load_balancer_egress_ip_protocol" {
  type        = string
  default     = "-1"
  description = "IP protocol for the outbound traffic of the load balancer (-1 means all)"
}

variable "load_balancer_listener_port" {
  type        = number
  default     = 80
  description = "Port on which the load balancer listens"
}

variable "load_balancer_listener_protocol" {
  type        = string
  default     = "HTTP"
  description = "Protocol of the load balancer listener and target group"
}

variable "load_balancer_target_group_name" {
  type        = string
  default     = "vela47-web-tg"
  description = "Name for the load balancer target group"
}

variable "load_balancer_health_check_path" {
  type        = string
  default     = "/"
  description = "Path which the load balancer checks for healthy EC2 instances"
}
