# Names of the resources, all derived from var.name
locals {
  app_name     = "${var.name}-app"
  sandbox_name = "${var.name}-sandbox"
}

# ECS cluster declaration (container insights stay off, they are billed per metric)
resource "aws_ecs_cluster" "this" {
  name = var.name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

# Log group declaration (what the server task prints, kept for log_retention_days)
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.app_name}"
  retention_in_days = var.log_retention_days
}

# Launch template declaration for the EC2 instances
# The ECS-optimized AMI only needs to know its cluster, user_data writes that into the agent's configuration,
# and tasks with their own network interface are kept away from the instance metadata, so they can only
# use the credentials of their task role
resource "aws_launch_template" "this" {
  name                   = var.name
  image_id               = var.instance_ami
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.instance.id]

  user_data = base64encode(<<-EOT
    #!/bin/bash
    cat >> /etc/ecs/ecs.config <<CONFIG
    ECS_CLUSTER=${aws_ecs_cluster.this.name}
    ECS_AWSVPC_BLOCK_IMDS=true
    CONFIG
  EOT
  )

  block_device_mappings {
    device_name = var.instance_root_device_name

    ebs {
      volume_size           = var.instance_root_volume_size
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  iam_instance_profile {
    arn = aws_iam_instance_profile.instance.arn
  }

  # IMDSv2 only, and only for the host: the ECS agent uses the host network, tasks get their credentials from ECS
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = var.instance_metadata_hop_limit
  }

  # Tags for the EC2 instances, not for the template itself
  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = var.name
    }
  }
}

# Auto scaling group declaration (EC2 instances live in the private subnets)
# A single instance, the group replaces it when it turns unhealthy. The load balancer checks the task, not the instance
resource "aws_autoscaling_group" "this" {
  name                      = var.name
  min_size                  = var.instance_min_count
  max_size                  = var.instance_max_count
  desired_capacity          = var.instance_desired_count
  vpc_zone_identifier       = var.private_subnet_ids
  health_check_type         = "EC2"
  health_check_grace_period = var.instance_health_check_grace_period

  launch_template {
    id      = aws_launch_template.this.id
    version = "$Latest"
  }

  # A new launch template version replaces the instance, the old one goes first since there is only one
  instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 0
    }
  }

  # The ECS agent needs the policies of the instance role, so on destroy they go after the instance;
  # without them the agent disconnects and a destroy waits forever on a task stuck in STOPPING.
  # The NAT gateway is in the vpc root module, which is destroyed after this one
  depends_on = [
    aws_iam_role_policy_attachment.instance_container_service,
    aws_iam_role_policy_attachment.instance_session_manager,
    aws_iam_instance_profile.instance,
  ]
}

# Task definition declaration (the server container, its image pinned by digest)
# awsvpc gives the task an interface and a security group of its own, the models and the sandbox are reached with the task role
resource "aws_ecs_task_definition" "this" {
  family                   = local.app_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([{
    name              = var.container_name
    image             = local.app_image
    essential         = true
    cpu               = var.task_cpu
    memory            = var.task_memory
    memoryReservation = var.task_memory_reservation
    portMappings      = [{ containerPort = var.container_port, protocol = "tcp" }]
    environment = [
      { name = "VELA47_ENVIRONMENT", value = "prod" },
      { name = "VELA47_AWS_REGION", value = var.region },
      { name = "VELA47_DATABASE_HOST", value = var.database_address },
      { name = "VELA47_DATABASE_PORT", value = tostring(var.database_port) },
      { name = "VELA47_DATABASE_NAME", value = var.database_name },
      { name = "VELA47_DATABASE_SECRET_ID", value = var.database_secret_arn },
      { name = "VELA47_APP_SECRET_ID", value = aws_secretsmanager_secret.app.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = var.container_name
      }
    }
  }])
}

# Service declaration (keeps the server task running behind the load balancer)
# A deploy starts the new task next to the old one and stops the old one once the new one is healthy,
# a deploy that never turns healthy is rolled back
resource "aws_ecs_service" "this" {
  name                              = local.app_name
  cluster                           = aws_ecs_cluster.this.id
  task_definition                   = aws_ecs_task_definition.this.arn
  desired_count                     = var.task_desired_count
  launch_type                       = "EC2"
  health_check_grace_period_seconds = var.task_health_check_grace_period
  wait_for_steady_state             = true

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.task.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = var.container_name
    container_port   = var.container_port
  }

  depends_on = [
    aws_lb_listener.https,
    aws_autoscaling_group.this,
    aws_iam_role_policy.task,
  ]
}
