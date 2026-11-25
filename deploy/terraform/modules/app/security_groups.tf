# Security group declarations
# The server task has a security group of its own, the instance under it takes no inbound traffic at all
resource "aws_security_group" "load_balancer" {
  name        = "${var.name}-load-balancer"
  description = "Security group of the load balancer"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name}-load-balancer"
  }
}

resource "aws_security_group" "instance" {
  name        = "${var.name}-instance"
  description = "Security group of the EC2 instance the server task runs on"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name}-instance"
  }
}

resource "aws_security_group" "task" {
  name        = "${local.app_name}-task"
  description = "Security group of the server task"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.app_name}-task"
  }
}

# Inbound and outbound traffic rules for the load balancer
# HTTP is only redirected to HTTPS
resource "aws_vpc_security_group_ingress_rule" "load_balancer_http" {
  security_group_id = aws_security_group.load_balancer.id
  cidr_ipv4         = var.load_balancer_ingress_cidr_ipv4
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "load_balancer_https" {
  security_group_id = aws_security_group.load_balancer.id
  cidr_ipv4         = var.load_balancer_ingress_cidr_ipv4
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "load_balancer_all" {
  security_group_id = aws_security_group.load_balancer.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# Outbound traffic rule for the EC2 instance (the ECS agent, ECR, CloudWatch Logs and Session Manager)
resource "aws_vpc_security_group_egress_rule" "instance_all" {
  security_group_id = aws_security_group.instance.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# Inbound and outbound traffic rules for the server task
# Inbound traffic is allowed only from the load balancer, outbound goes through the NAT (Bedrock, the web tools)
resource "aws_vpc_security_group_ingress_rule" "task_from_load_balancer" {
  security_group_id            = aws_security_group.task.id
  referenced_security_group_id = aws_security_group.load_balancer.id
  ip_protocol                  = "tcp"
  from_port                    = var.container_port
  to_port                      = var.container_port
}

resource "aws_vpc_security_group_egress_rule" "task_all" {
  security_group_id = aws_security_group.task.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# Inbound traffic rule for the database (its security group belongs to the database root module)
# PostgreSQL is reachable only from the server task, the database opens no connections itself
resource "aws_vpc_security_group_ingress_rule" "database_from_task" {
  security_group_id            = var.database_security_group_id
  referenced_security_group_id = aws_security_group.task.id
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
}
