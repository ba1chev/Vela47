# Office hours of an environment nobody uses at night: EventBridge Scheduler stops the server tasks and the database in the
# evening and starts them in the morning, so the capacity provider scales the instances to 0 in between. A deployment
# outside these hours starts the database first and Terraform sets the task count back
locals {
  schedules = {
    stop_service = {
      expression = var.stop_expression
      target     = "arn:aws:scheduler:::aws-sdk:ecs:updateService"
      input      = { Cluster = var.cluster_name, Service = var.service_name, DesiredCount = 0 }
    }
    stop_database = {
      expression = var.stop_database_expression
      target     = "arn:aws:scheduler:::aws-sdk:rds:stopDBInstance"
      input      = { DbInstanceIdentifier = var.db_instance_identifier }
    }
    start_database = {
      expression = var.start_database_expression
      target     = "arn:aws:scheduler:::aws-sdk:rds:startDBInstance"
      input      = { DbInstanceIdentifier = var.db_instance_identifier }
    }
    start_service = {
      expression = var.start_expression
      target     = "arn:aws:scheduler:::aws-sdk:ecs:updateService"
      input      = { Cluster = var.cluster_name, Service = var.service_name, DesiredCount = var.desired_count }
    }
  }
}

# IAM role declaration for the scheduler, it may only change the task count of the service and stop or start the database
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name                 = "${var.name}-schedule"
  assume_role_policy   = data.aws_iam_policy_document.assume_role.json
  permissions_boundary = var.permissions_boundary_arn
}

data "aws_iam_policy_document" "this" {
  statement {
    actions   = ["ecs:UpdateService"]
    resources = [var.service_arn]
  }

  statement {
    actions   = ["rds:StopDBInstance", "rds:StartDBInstance"]
    resources = [var.db_instance_arn]
  }
}

resource "aws_iam_role_policy" "this" {
  name   = "${var.name}-schedule"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.this.json
}

# Schedule declarations, one per action, in the time zone of the people who use the environment
resource "aws_scheduler_schedule" "this" {
  for_each = local.schedules

  name                         = "${var.name}-${replace(each.key, "_", "-")}"
  schedule_expression          = each.value.expression
  schedule_expression_timezone = var.timezone

  flexible_time_window {
    mode = "OFF"
  }

  #checkov:skip=CKV_AWS_297:The input names a cluster, a service and a database, nothing a customer managed key would protect

  target {
    arn      = each.value.target
    role_arn = aws_iam_role.this.arn
    input    = jsonencode(each.value.input)

    retry_policy {
      maximum_retry_attempts = 3
    }
  }
}
