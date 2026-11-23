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

  # The instance reaches ECS only through the NAT gateway and with the policies of its role, so on destroy the gateway,
  # its route and the role's policies go after the instance; without them the ECS agent disconnects and a destroy
  # waits forever on a task stuck in STOPPING
  depends_on = [
    aws_nat_gateway.main,
    aws_route_table_association.private,
    aws_iam_role_policy_attachment.ec2_container_service,
    aws_iam_role_policy_attachment.ec2_session_manager,
    aws_iam_instance_profile.ec2,
  ]

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
