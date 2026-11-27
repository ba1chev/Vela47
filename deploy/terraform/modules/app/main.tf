# Names of the resources, all derived from var.name, and the deployment strategy of the service
locals {
  app_name     = "${var.name}-app"
  sandbox_name = "${var.name}-sandbox"
  canary       = var.deployment_strategy == "CANARY"
}

# ECS cluster declaration (container insights stay off, they are billed per metric)
resource "aws_ecs_cluster" "this" {
  name = var.name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  #checkov:skip=CKV_AWS_65:Container Insights are billed per metric, the load balancer and ECS metrics are enough here
}

# Log group declaration (what the server task prints, kept for log_retention_days)
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.app_name}"
  retention_in_days = var.log_retention_days

  #checkov:skip=CKV_AWS_158:The logs are encrypted by CloudWatch, a customer managed KMS key is not worth its price here
  #checkov:skip=CKV_AWS_338:Logs are kept for log_retention_days, a year of them is not needed
}

# Launch template declaration for the EC2 instances
# The ECS-optimized AMI only needs to know its cluster, user_data writes that into the agent's configuration,
# and tasks with their own network interface are kept away from the instance metadata, so they can only
# use the credentials of their task role. The AMI is resolved when an instance launches, so every new
# instance, and every instance replaced at instance_max_lifetime, starts from the newest patched image
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
# ECS sizes it through the capacity provider below, so its desired capacity is not Terraform's. An instance is
# replaced after instance_max_lifetime, and a replacement always starts before the old instance stops
resource "aws_autoscaling_group" "this" {
  name                      = var.name
  min_size                  = var.instance_min_count
  max_size                  = var.instance_max_count
  vpc_zone_identifier       = var.private_subnet_ids
  health_check_type         = "EC2"
  health_check_grace_period = var.instance_health_check_grace_period
  max_instance_lifetime     = var.instance_max_lifetime

  launch_template {
    id      = aws_launch_template.this.id
    version = "$Latest"
  }

  instance_maintenance_policy {
    min_healthy_percentage = 100
    max_healthy_percentage = 200
  }

  # A new launch template version replaces the instances, new ones first (see instance_maintenance_policy)
  instance_refresh {
    strategy = "Rolling"
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = "true"
    propagate_at_launch = true
  }

  # The ECS agent needs the policies of the instance role and the way out of its security group, so on destroy they go
  # after the instance; without either the agent disconnects and a destroy waits forever on a task stuck in STOPPING.
  # The NAT is in the vpc root module, which is destroyed after this one
  depends_on = [
    aws_iam_role_policy_attachment.instance_container_service,
    aws_iam_role_policy_attachment.instance_session_manager,
    aws_iam_instance_profile.instance,
    aws_vpc_security_group_egress_rule.instance_all,
  ]

  lifecycle {
    ignore_changes = [desired_capacity]
  }
}

# Capacity provider declaration (ECS adds an instance when tasks do not fit, a blue/green deployment needs twice the tasks)
resource "aws_ecs_capacity_provider" "this" {
  name = var.name

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.this.arn
    managed_termination_protection = "DISABLED"
    managed_draining               = "ENABLED"

    managed_scaling {
      status                    = "ENABLED"
      target_capacity           = 100
      minimum_scaling_step_size = 1
      maximum_scaling_step_size = 1
    }
  }
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = [aws_ecs_capacity_provider.this.name]

  default_capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.this.name
    weight            = 1
  }
}

# Task definition declaration (the server container of the release, its image pinned by digest)
# awsvpc gives the task an interface and a security group of its own, the models and the sandbox are reached with the
# task role. On a stop the server gets task_stop_timeout seconds to finish the answers it is streaming
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
    image             = var.app_image
    essential         = true
    cpu               = var.task_cpu
    memory            = var.task_memory
    memoryReservation = var.task_memory_reservation
    stopTimeout       = var.task_stop_timeout
    portMappings      = [{ containerPort = var.container_port, protocol = "tcp" }]
    linuxParameters   = { initProcessEnabled = true }
    environment = [
      { name = "VELA47_ENVIRONMENT", value = var.environment },
      { name = "VELA47_VERSION", value = var.release_version },
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

  #checkov:skip=CKV_AWS_336:Every agent run keeps its files in a directory under /tmp, which a read-only root would need as tmpfs out of the task memory
}

# Service declaration (keeps the server tasks running behind the load balancer)
# ROLLING starts new tasks beside the old ones and stops the old ones once the new ones are healthy. CANARY starts a full
# set of new tasks in the second target group, moves canary_percent of the traffic to them, then all of it, and keeps the
# old tasks for bake_time_minutes so a rollback is instant. Either way an alarm going off during the deployment rolls it
# back. The deployment workflow follows it and runs the smoke test, so Terraform does not wait for it
resource "aws_ecs_service" "this" {
  name                              = local.app_name
  cluster                           = aws_ecs_cluster.this.id
  task_definition                   = aws_ecs_task_definition.this.arn
  desired_count                     = var.task_desired_count
  health_check_grace_period_seconds = var.task_health_check_grace_period
  enable_execute_command            = true
  enable_ecs_managed_tags           = true
  propagate_tags                    = "SERVICE"
  wait_for_steady_state             = false

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.this.name
    weight            = 1
  }

  deployment_configuration {
    strategy             = var.deployment_strategy
    bake_time_in_minutes = local.canary ? var.bake_time_minutes : null

    dynamic "canary_configuration" {
      for_each = local.canary ? [1] : []

      content {
        canary_percent              = var.canary_percent
        canary_bake_time_in_minutes = var.canary_bake_time_minutes
      }
    }
  }

  dynamic "deployment_circuit_breaker" {
    for_each = local.canary ? [] : [1]

    content {
      enable   = true
      rollback = true
    }
  }

  alarms {
    alarm_names = concat([aws_cloudwatch_metric_alarm.target_5xx.alarm_name], [for current in aws_cloudwatch_metric_alarm.unhealthy_hosts : current.alarm_name])
    enable      = true
    rollback    = true
  }

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.task.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this["blue"].arn
    container_name   = var.container_name
    container_port   = var.container_port

    dynamic "advanced_configuration" {
      for_each = local.canary ? [1] : []

      content {
        alternate_target_group_arn = aws_lb_target_group.this["green"].arn
        production_listener_rule   = aws_lb_listener_rule.app.arn
        role_arn                   = aws_iam_role.ecs_infrastructure[0].arn
      }
    }
  }

  depends_on = [
    aws_lb_listener_rule.app,
    aws_ecs_cluster_capacity_providers.this,
    aws_iam_role_policy.task,
    aws_iam_role_policy_attachment.ecs_infrastructure,
    aws_vpc_security_group_ingress_rule.task_from_load_balancer,
    aws_vpc_security_group_egress_rule.task_all,
  ]

  # After a canary deployment ECS serves from the other target group, so the load balancer of the service is ECS's,
  # not Terraform's: sending it back on the next update would put the new tasks next to the live ones.
  # Switching deployment_strategy therefore needs the service replaced (terraform apply -replace)
  lifecycle {
    ignore_changes = [load_balancer]
  }
}
