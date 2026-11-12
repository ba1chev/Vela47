terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Tags shared by all tagged resources
locals {
  common_tags = {
    Name        = var.resource_name_tag
    Environment = var.environment_tag
  }
}

# Availability zones declaration (read only)
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC declaration
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
}

# Internet gateway declaration (internet access for the public subnets)
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

# VPC subnet declaration (public + private)
# Public subnets hold the load balancer and the NAT gateway
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidr_blocks)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr_blocks[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
}

# Private subnets hold the EC2 instances (not reachable from the internet)
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidr_blocks)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

# Public route table declaration (all outbound traffic goes to the internet gateway)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT declaration (outbound only internet access for the private subnets)
resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  # NAT gateway needs the internet gateway, Terraform can not see this by itself
  depends_on = [aws_internet_gateway.main]
}

# Private route table declaration (all outbound traffic goes to the NAT gateway)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security groups
resource "aws_security_group" "web" {
  name        = var.ec2_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the EC2 server instance"
  tags        = local.common_tags
}

resource "aws_security_group" "lb_sg" {
  name        = var.elb_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the ALB"
  tags        = local.common_tags
}

# Inbound and outbound traffic rules for the EC2 instances
# Inbound traffic is allowed only from the load balancer security group
resource "aws_vpc_security_group_ingress_rule" "web_from_lb" {
  security_group_id            = aws_security_group.web.id
  referenced_security_group_id = aws_security_group.lb_sg.id
  ip_protocol                  = "tcp"
  from_port                    = var.ec2_instance_http_port
  to_port                      = var.ec2_instance_http_port
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.web.id
  cidr_ipv4         = var.ec2_instance_egress_cidr_ipv4
  ip_protocol       = var.ec2_instance_egress_ip_protocol
}

# Inbound and outbound traffic rules for the load balancer
resource "aws_vpc_security_group_ingress_rule" "lb_http" {
  security_group_id = aws_security_group.lb_sg.id
  cidr_ipv4         = var.load_balancer_ingress_cidr_ipv4
  ip_protocol       = "tcp"
  from_port         = var.load_balancer_listener_port
  to_port           = var.load_balancer_listener_port
}

resource "aws_vpc_security_group_egress_rule" "lb_all" {
  security_group_id = aws_security_group.lb_sg.id
  cidr_ipv4         = var.load_balancer_egress_cidr_ipv4
  ip_protocol       = var.load_balancer_egress_ip_protocol
}

# Launch EC2 instances template declaration
resource "aws_launch_template" "web" {
  name                   = var.ec2_launch_template_name
  image_id               = var.ec2_instance_ami
  instance_type          = var.ec2_instance_type
  vpc_security_group_ids = [aws_security_group.web.id]

  # Tags for the EC2 instances, not for the template itself
  tag_specifications {
    resource_type = "instance"
    tags          = local.common_tags
  }
}

# Auto scaling group declaration (EC2 instances live in the private subnets)
resource "aws_autoscaling_group" "web" {
  min_size            = var.ec2_launch_template_min_instances
  max_size            = var.ec2_launch_template_max_instances
  desired_capacity    = var.ec2_launch_template_desired_instances
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.web.arn]
  health_check_type   = var.ec2_autoscaling_health_check_type

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }
}

# Load balancer instance declaration (lives in the public subnets)
resource "aws_lb" "load_balancer" {
  name                       = var.load_balancer_name
  load_balancer_type         = var.load_balancer_type
  security_groups            = [aws_security_group.lb_sg.id]
  subnets                    = aws_subnet.public[*].id
  internal                   = var.load_balancer_internal
  enable_deletion_protection = var.load_balancer_deletion_protection
  tags                       = local.common_tags
}

# Target group declaration (the EC2 instances which receive the traffic)
resource "aws_lb_target_group" "web" {
  name     = var.load_balancer_target_group_name
  port     = var.ec2_instance_http_port
  protocol = var.load_balancer_listener_protocol
  vpc_id   = aws_vpc.main.id

  health_check {
    path = var.load_balancer_health_check_path
  }
}

# Listener declaration (forwards the incoming traffic to the target group)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.load_balancer.arn
  port              = var.load_balancer_listener_port
  protocol          = var.load_balancer_listener_protocol

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}
