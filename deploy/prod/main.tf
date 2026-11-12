terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.9.1"
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

resource "aws_security_group" "database" {
  name        = var.rds_security_group_name
  vpc_id      = aws_vpc.main.id
  description = "Security group for the RDS instance"
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

# Database subnet group declaration (Multi-AZ needs subnets in at least 2 availability zones)
resource "aws_db_subnet_group" "database" {
  name       = var.rds_subnet_group_name
  subnet_ids = aws_subnet.private[*].id
  tags       = local.common_tags
}

# RDS PostgreSQL instance declaration (primary + standby in another availability zone, lives in the private subnets)
# RDS creates the master password itself and keeps it in a Secrets Manager secret which it rotates,
# the server reads that secret for every new connection
resource "aws_db_instance" "database" {
  identifier     = var.rds_instance_identifier
  engine         = var.rds_engine
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class

  allocated_storage = var.rds_allocated_storage
  storage_type      = var.rds_storage_type
  storage_encrypted = var.rds_storage_encrypted

  db_name                     = var.rds_database_name
  username                    = var.rds_master_username
  manage_master_user_password = true
  port                        = var.rds_port

  multi_az               = var.rds_multi_az
  db_subnet_group_name   = aws_db_subnet_group.database.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = var.rds_publicly_accessible

  backup_retention_period = var.rds_backup_retention_period
  skip_final_snapshot     = var.rds_skip_final_snapshot
  deletion_protection     = var.rds_deletion_protection
  tags                    = local.common_tags
}

# Application secret declaration (token signing key and the admin bootstrapped on the first start)
# The server reads it once at startup, VELA47_APP_SECRET_ID points to it
resource "random_password" "token_secret" {
  length  = var.app_token_secret_length
  special = false
}

resource "random_password" "admin_password" {
  length  = var.app_admin_password_length
  special = false
}

resource "aws_secretsmanager_secret" "app" {
  name                    = var.app_secret_name
  recovery_window_in_days = var.app_secret_recovery_window_in_days
  tags                    = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    token_secret   = random_password.token_secret.result
    admin_username = var.app_admin_username
    admin_password = random_password.admin_password.result
  })
}

# IAM role declaration for the EC2 instances
# The server never calls the RDS API, it only reads the application secret and the database secret
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = var.ec2_iam_role_name
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "ec2_read_secrets" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.app.arn,
      aws_db_instance.database.master_user_secret[0].secret_arn,
    ]
  }
}

resource "aws_iam_role_policy" "ec2_read_secrets" {
  name   = var.ec2_iam_policy_name
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ec2_read_secrets.json
}

# Session Manager access (aws ssm start-session reaches the instance without SSH or a public address)
resource "aws_iam_role_policy_attachment" "ec2_session_manager" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance profile declaration (how the IAM role is handed to the EC2 instances)
resource "aws_iam_instance_profile" "ec2" {
  name = var.ec2_instance_profile_name
  role = aws_iam_role.ec2.name
}

# Launch EC2 instances template declaration
# One GPU instance runs the server, Ollama and the sandbox containers; user_data sets it all up on the first boot
resource "aws_launch_template" "web" {
  name                   = var.ec2_launch_template_name
  image_id               = var.ec2_instance_ami
  instance_type          = var.ec2_instance_type
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = base64encode(templatefile("${path.module}/scripts/user_data.sh.tftpl", {
    aws_region            = var.aws_region
    app_network_name      = var.app_network_name
    app_network_subnet    = var.app_network_subnet
    app_image_name        = var.app_image_name
    app_container_name    = var.app_container_name
    app_port              = var.ec2_instance_http_port
    repository_url        = var.app_repository_url
    repository_branch     = var.app_repository_branch
    ollama_image          = var.ollama_image
    ollama_container_name = var.ollama_container_name
    ollama_volume_name    = var.ollama_volume_name
    ollama_models         = join(" ", var.ollama_models)
    database_host         = aws_db_instance.database.address
    database_port         = var.rds_port
    database_name         = var.rds_database_name
    database_secret_id    = aws_db_instance.database.master_user_secret[0].secret_arn
    app_secret_id         = aws_secretsmanager_secret.app.arn
  }))

  # Room for the models, the images and the Docker build cache
  block_device_mappings {
    device_name = var.ec2_instance_root_device_name

    ebs {
      volume_size           = var.ec2_instance_root_volume_size
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  iam_instance_profile {
    arn = aws_iam_instance_profile.ec2.arn
  }

  # IMDSv2 only, the server runs in a container which is one hop further from the metadata service than the host
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = var.ec2_instance_metadata_hop_limit
  }

  # Tags for the EC2 instances, not for the template itself
  tag_specifications {
    resource_type = "instance"
    tags          = local.common_tags
  }
}

# Auto scaling group declaration (EC2 instances live in the private subnets)
# A single instance, the group replaces it when it turns unhealthy. The first boot pulls the models and builds
# the server, so the grace period has to cover it before failed health checks count
resource "aws_autoscaling_group" "web" {
  min_size                  = var.ec2_launch_template_min_instances
  max_size                  = var.ec2_launch_template_max_instances
  desired_capacity          = var.ec2_launch_template_desired_instances
  vpc_zone_identifier       = aws_subnet.private[*].id
  target_group_arns         = [aws_lb_target_group.web.arn]
  health_check_type         = var.ec2_autoscaling_health_check_type
  health_check_grace_period = var.ec2_autoscaling_health_check_grace_period

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  # A new launch template version replaces the instance, the old one goes first since there is only one
  instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 0
    }
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
  idle_timeout               = var.load_balancer_idle_timeout
  tags                       = local.common_tags
}

# Target group declaration (the EC2 instances which receive the traffic)
resource "aws_lb_target_group" "web" {
  name     = var.load_balancer_target_group_name
  port     = var.ec2_instance_http_port
  protocol = var.load_balancer_target_group_protocol
  vpc_id   = aws_vpc.main.id

  health_check {
    path = var.load_balancer_health_check_path
  }
}

# Listener declarations
# HTTP only redirects, the session cookie is Secure in production and a browser sends it over HTTPS only
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.load_balancer.arn
  port              = var.load_balancer_listener_port
  protocol          = var.load_balancer_listener_protocol

  default_action {
    type = "redirect"

    redirect {
      port        = tostring(var.load_balancer_https_listener_port)
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS ends at the load balancer and forwards the incoming traffic to the target group
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.load_balancer.arn
  port              = var.load_balancer_https_listener_port
  protocol          = "HTTPS"
  ssl_policy        = var.load_balancer_ssl_policy
  certificate_arn   = aws_acm_certificate_validation.app.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# Hosted zone declaration (read only, the zone already exists in the account)
data "aws_route53_zone" "main" {
  name = var.route53_zone_name
}

# Certificate declaration (issued by ACM for the application domain, validated through a DNS record in the zone)
resource "aws_acm_certificate" "app" {
  domain_name       = var.app_domain_name
  validation_method = "DNS"
  tags              = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "certificate_validation" {
  for_each = {
    for current in aws_acm_certificate.app.domain_validation_options : current.domain_name => current
  }

  zone_id         = data.aws_route53_zone.main.zone_id
  name            = each.value.resource_record_name
  type            = each.value.resource_record_type
  records         = [each.value.resource_record_value]
  ttl             = 60
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "app" {
  certificate_arn         = aws_acm_certificate.app.arn
  validation_record_fqdns = [for current in aws_route53_record.certificate_validation : current.fqdn]
}

# DNS record declaration (the application domain points at the load balancer)
resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.app_domain_name
  type    = "A"

  alias {
    name                   = aws_lb.load_balancer.dns_name
    zone_id                = aws_lb.load_balancer.zone_id
    evaluate_target_health = true
  }
}
