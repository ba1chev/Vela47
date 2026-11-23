# Security groups
# The server task has a security group of its own, the instance under it takes no inbound traffic at all
resource "aws_security_group" "web" {
  name        = var.app_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the server task"
  tags        = local.common_tags
}

resource "aws_security_group" "ecs_instance" {
  name        = var.ec2_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the EC2 instance the server task runs on"
  tags        = local.common_tags
}

resource "aws_security_group" "lb_sg" {
  name        = var.elb_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the ALB"
  tags        = local.common_tags
}

resource "aws_security_group" "database" {
  name        = var.rds_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the RDS instance"
  tags        = local.common_tags
}

# The sandbox function runs code a model wrote, its security group has no rule, so nothing reaches it and it reaches nothing
# An empty egress list removes the allow-all rule AWS adds to every new security group
resource "aws_security_group" "sandbox" {
  name        = var.sandbox_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the sandbox function, no traffic in or out"
  egress      = []
  tags        = local.common_tags
}

# Inbound and outbound traffic rules for the server task
# Inbound traffic is allowed only from the load balancer security group, outbound goes through the NAT (Bedrock, the web tools)
resource "aws_vpc_security_group_ingress_rule" "web_from_lb" {
  security_group_id            = aws_security_group.web.id
  referenced_security_group_id = aws_security_group.lb_sg.id
  ip_protocol                  = "tcp"
  from_port                    = var.app_container_port
  to_port                      = var.app_container_port
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.web.id
  cidr_ipv4         = var.ec2_instance_egress_cidr_ipv4
  ip_protocol       = var.ec2_instance_egress_ip_protocol
}

# Outbound traffic rule for the EC2 instance (the ECS agent, ECR, CloudWatch Logs and Session Manager)
resource "aws_vpc_security_group_egress_rule" "ecs_instance_all" {
  security_group_id = aws_security_group.ecs_instance.id
  cidr_ipv4         = var.ec2_instance_egress_cidr_ipv4
  ip_protocol       = var.ec2_instance_egress_ip_protocol
}

# Inbound and outbound traffic rules for the load balancer
# HTTP is only redirected to HTTPS
resource "aws_vpc_security_group_ingress_rule" "lb_http" {
  security_group_id = aws_security_group.lb_sg.id
  cidr_ipv4         = var.load_balancer_ingress_cidr_ipv4
  ip_protocol       = "tcp"
  from_port         = var.load_balancer_listener_port
  to_port           = var.load_balancer_listener_port
}

resource "aws_vpc_security_group_ingress_rule" "lb_https" {
  security_group_id = aws_security_group.lb_sg.id
  cidr_ipv4         = var.load_balancer_ingress_cidr_ipv4
  ip_protocol       = "tcp"
  from_port         = var.load_balancer_https_listener_port
  to_port           = var.load_balancer_https_listener_port
}

resource "aws_vpc_security_group_egress_rule" "lb_all" {
  security_group_id = aws_security_group.lb_sg.id
  cidr_ipv4         = var.load_balancer_egress_cidr_ipv4
  ip_protocol       = var.load_balancer_egress_ip_protocol
}

# Inbound traffic rule for the database
# PostgreSQL is reachable only from the EC2 instances security group, the database opens no connections itself
resource "aws_vpc_security_group_ingress_rule" "database_from_web" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.web.id
  ip_protocol                  = "tcp"
  from_port                    = var.rds_port
  to_port                      = var.rds_port
}
