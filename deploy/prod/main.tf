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
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Docker builds the two images on this machine and pushes them to ECR with a short-lived token
# Docker Desktop on a Mac has no /var/run/docker.sock, the provider reaches it through its context
data "aws_ecr_authorization_token" "main" {}

provider "docker" {
  context = var.docker_context

  registry_auth {
    address  = replace(data.aws_ecr_authorization_token.main.proxy_endpoint, "https://", "")
    username = data.aws_ecr_authorization_token.main.user_name
    password = data.aws_ecr_authorization_token.main.password
  }
}

# Tags shared by all tagged resources
locals {
  common_tags = {
    Name        = var.resource_name_tag
    Environment = var.environment_tag
  }
}

# Bedrock models the server task may call
# An ID with a geography prefix (eu.) is an inference profile, which routes a request to one of several regions,
# so the task needs the profile itself and the base model in every region it can be routed to
data "aws_caller_identity" "current" {}

locals {
  bedrock_base_model_ids = [for current in var.bedrock_model_ids : replace(current, "/^(eu|us|apac|global)\\./", "")]
  bedrock_resources = concat(
    [for current in local.bedrock_base_model_ids : "arn:aws:bedrock:*::foundation-model/${current}"],
    [
      for current in var.bedrock_model_ids : "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/${current}"
      if !contains(local.bedrock_base_model_ids, current)
    ]
  )
}

# Paths of the images, and the files whose change rebuilds each of them
# An image is tagged with a hash of its files, so a change gives a new tag and ECS deploys it
locals {
  repository      = abspath("${path.module}/../..")
  app_dockerfile  = "deploy/prod/images/app_image/Dockerfile"
  sandbox_context = "${local.repository}/deploy/prod/images/sandbox_lambda"
  app_source_files = sort([
    for current_file in setunion(
      fileset(local.repository, "app/**"),
      fileset(local.repository, "db/**"),
      ["requirements.txt", local.app_dockerfile]
    ) : current_file if !strcontains(current_file, "__pycache__") && !strcontains(current_file, ".sqlite3")
  ])
  app_image_tag = substr(sha1(join("", [
    for current_file in local.app_source_files : filesha1("${local.repository}/${current_file}")
  ])), 0, 12)
  sandbox_image_tag = substr(sha1(join("", [
    for current_file in sort(fileset(local.sandbox_context, "*")) : filesha1("${local.sandbox_context}/${current_file}")
  ])), 0, 12)
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

# Database subnet group declaration (subnets in 2 availability zones, which Multi-AZ needs once it is turned on)
resource "aws_db_subnet_group" "database" {
  name       = var.rds_subnet_group_name
  subnet_ids = aws_subnet.private[*].id
  tags       = local.common_tags
}

# RDS PostgreSQL instance declaration (lives in the private subnets, rds_multi_az adds a standby in another availability zone)
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

# ECR repository declarations (the server image and the sandbox function image)
# force_delete lets terraform destroy remove a repository that still holds images
resource "aws_ecr_repository" "app" {
  name                 = var.app_repository_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
  tags                 = local.common_tags
}

resource "aws_ecr_repository" "sandbox" {
  name                 = var.sandbox_repository_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
  tags                 = local.common_tags
}

# Only the newest images are kept, the older ones are deleted
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the newest images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = var.ecr_kept_images }
      action       = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "sandbox" {
  repository = aws_ecr_repository.sandbox.name
  policy     = aws_ecr_lifecycle_policy.app.policy
}

# Image declarations (built here for arm64, the Graviton instance and the Lambda function both run on it, then pushed)
# Without provenance and SBOM attestations BuildKit writes a single image manifest instead of an index around it,
# the only form Lambda accepts
resource "docker_image" "app" {
  name = "${aws_ecr_repository.app.repository_url}:${local.app_image_tag}"

  build {
    context    = local.repository
    dockerfile = local.app_dockerfile
    platform   = "linux/arm64"
    provenance = "false"
    sbom       = "false"
  }
}

resource "docker_registry_image" "app" {
  name          = docker_image.app.name
  keep_remotely = true
}

resource "docker_image" "sandbox" {
  name = "${aws_ecr_repository.sandbox.repository_url}:${local.sandbox_image_tag}"

  build {
    context    = local.sandbox_context
    platform   = "linux/arm64"
    provenance = "false"
    sbom       = "false"
  }
}

resource "docker_registry_image" "sandbox" {
  name          = docker_image.sandbox.name
  keep_remotely = true
}

# Log group declarations (what the server task and the sandbox function print, kept for log_retention_days)
resource "aws_cloudwatch_log_group" "app" {
  name              = var.app_log_group_name
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "sandbox" {
  name              = "/aws/lambda/${var.sandbox_function_name}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# IAM role declaration for the EC2 instances
# The instance only runs the ECS agent, which registers it in the cluster, Session Manager reaches it without SSH
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

resource "aws_iam_role_policy_attachment" "ec2_container_service" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ec2_session_manager" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance profile declaration (how the IAM role is handed to the EC2 instances)
resource "aws_iam_instance_profile" "ec2" {
  name = var.ec2_instance_profile_name
  role = aws_iam_role.ec2.name
}

# IAM role declarations for the server task
# ECS pulls the image and writes the logs with the execution role, the server itself runs with the task role
data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = var.ecs_task_execution_role_name
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name               = var.ecs_task_role_name
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
  tags               = local.common_tags
}

# The server reads the two secrets, calls the models it is configured with and runs commands in the sandbox function, nothing else
data "aws_iam_policy_document" "ecs_task" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.app.arn,
      aws_db_instance.database.master_user_secret[0].secret_arn,
    ]
  }

  statement {
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = local.bedrock_resources
  }

  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.sandbox.arn]
  }
}

resource "aws_iam_role_policy" "ecs_task" {
  name   = var.ecs_task_policy_name
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task.json
}

# IAM role declaration for the sandbox function
# It may only write its logs and attach to the VPC, so code it runs has no permission to call anything in AWS
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sandbox" {
  name               = var.sandbox_role_name
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "sandbox_vpc_access" {
  role       = aws_iam_role.sandbox.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Sandbox function declaration (lives in the private subnets behind a security group without rules, see SandboxLambda)
# One command per invocation over a copy of the run's workspace, every invocation in a microVM of its own
resource "aws_lambda_function" "sandbox" {
  function_name = var.sandbox_function_name
  role          = aws_iam_role.sandbox.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.sandbox.repository_url}@${docker_registry_image.sandbox.sha256_digest}"
  architectures = ["arm64"]
  memory_size   = var.sandbox_memory_size
  timeout       = var.sandbox_timeout
  tags          = local.common_tags

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.sandbox.id]
  }

  depends_on = [aws_cloudwatch_log_group.sandbox, aws_iam_role_policy_attachment.sandbox_vpc_access]
}

# ECS cluster declaration (container insights stay off, they are billed per metric)
resource "aws_ecs_cluster" "main" {
  name = var.ecs_cluster_name
  tags = local.common_tags

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

# Launch EC2 instances template declaration
# The ECS-optimized AMI only needs to know its cluster, user_data writes that into the agent's configuration
resource "aws_launch_template" "web" {
  name                   = var.ec2_launch_template_name
  image_id               = var.ec2_instance_ami
  instance_type          = var.ec2_instance_type
  vpc_security_group_ids = [aws_security_group.ecs_instance.id]

  user_data = base64encode(templatefile("${path.module}/scripts/user_data.sh", {
    cluster_name = aws_ecs_cluster.main.name
  }))

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

  # IMDSv2 only, and only for the host: the ECS agent uses the host network, tasks get their credentials from ECS
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
# A single instance, the group replaces it when it turns unhealthy. The load balancer checks the task, not the instance
resource "aws_autoscaling_group" "web" {
  min_size                  = var.ec2_launch_template_min_instances
  max_size                  = var.ec2_launch_template_max_instances
  desired_capacity          = var.ec2_launch_template_desired_instances
  vpc_zone_identifier       = aws_subnet.private[*].id
  health_check_type         = var.ec2_autoscaling_health_check_type
  health_check_grace_period = var.ec2_autoscaling_health_check_grace_period

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  # The instance reaches ECS only through the NAT gateway, so the gateway and its route go after the instance on destroy
  depends_on = [aws_nat_gateway.main, aws_route_table_association.private]

  # A new launch template version replaces the instance, the old one goes first since there is only one
  instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 0
    }
  }
}

# Task definition declaration (the server container, its image pinned by digest)
# awsvpc gives the task an interface and a security group of its own, the models and the sandbox are reached with the task role
resource "aws_ecs_task_definition" "app" {
  family                   = var.ecs_task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  tags                     = local.common_tags

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([{
    name              = var.app_container_name
    image             = "${aws_ecr_repository.app.repository_url}@${docker_registry_image.app.sha256_digest}"
    essential         = true
    cpu               = var.ecs_task_cpu
    memory            = var.ecs_task_memory
    memoryReservation = var.ecs_task_memory_reservation
    portMappings      = [{ containerPort = var.app_container_port, protocol = "tcp" }]
    environment = [
      { name = "VELA47_ENVIRONMENT", value = "prod" },
      { name = "VELA47_AWS_REGION", value = var.aws_region },
      { name = "VELA47_DATABASE_HOST", value = aws_db_instance.database.address },
      { name = "VELA47_DATABASE_PORT", value = tostring(var.rds_port) },
      { name = "VELA47_DATABASE_NAME", value = var.rds_database_name },
      { name = "VELA47_DATABASE_SECRET_ID", value = aws_db_instance.database.master_user_secret[0].secret_arn },
      { name = "VELA47_APP_SECRET_ID", value = aws_secretsmanager_secret.app.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = var.app_container_name
      }
    }
  }])
}

# Service declaration (keeps the server task running behind the load balancer)
# A deploy starts the new task next to the old one and stops the old one once the new one is healthy,
# a deploy that never turns healthy is rolled back
resource "aws_ecs_service" "app" {
  name                              = var.ecs_service_name
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.app.arn
  desired_count                     = var.ecs_desired_count
  launch_type                       = "EC2"
  health_check_grace_period_seconds = 60
  wait_for_steady_state             = true
  tags                              = local.common_tags

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.web.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = var.app_container_name
    container_port   = var.app_container_port
  }

  # The ECS agent confirms a stopped task through the NAT gateway; without it a destroy waits on a draining service forever
  depends_on = [
    aws_lb_listener.https,
    aws_autoscaling_group.web,
    aws_iam_role_policy.ecs_task,
    aws_nat_gateway.main,
    aws_route_table_association.private,
  ]
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

  # The internet gateway can only be detached once no public address is left in the VPC, so the load balancer goes first
  depends_on = [aws_internet_gateway.main]
}

# Target group declaration (the server tasks which receive the traffic, by the address of their own interface)
resource "aws_lb_target_group" "web" {
  name                 = var.load_balancer_target_group_name
  port                 = var.app_container_port
  protocol             = var.load_balancer_target_group_protocol
  target_type          = "ip"
  vpc_id               = aws_vpc.main.id
  deregistration_delay = 30

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
