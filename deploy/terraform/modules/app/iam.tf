# IAM role declaration for the EC2 instances
# The instance only runs the ECS agent, which registers it in the cluster, Session Manager reaches it without SSH
data "aws_iam_policy_document" "instance_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance" {
  name                 = "${var.name}-instance"
  assume_role_policy   = data.aws_iam_policy_document.instance_assume_role.json
  permissions_boundary = var.permissions_boundary_arn
}

resource "aws_iam_role_policy_attachment" "instance_container_service" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "instance_session_manager" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance profile declaration (how the IAM role is handed to the EC2 instances)
resource "aws_iam_instance_profile" "instance" {
  name = "${var.name}-instance"
  role = aws_iam_role.instance.name
}

# IAM role declarations for the server task
# ECS pulls the image and writes the logs with the execution role, the server itself runs with the task role
data "aws_iam_policy_document" "task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name                 = "${local.app_name}-task-execution"
  assume_role_policy   = data.aws_iam_policy_document.task_assume_role.json
  permissions_boundary = var.permissions_boundary_arn
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name                 = "${local.app_name}-task"
  assume_role_policy   = data.aws_iam_policy_document.task_assume_role.json
  permissions_boundary = var.permissions_boundary_arn
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
      for current in var.bedrock_model_ids : "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:inference-profile/${current}"
      if !contains(local.bedrock_base_model_ids, current)
    ]
  )
}

# The server reads the two secrets, calls the models it is configured with and runs commands in the sandbox function.
# ECS Exec opens a shell in the running task through Session Manager, for debugging only
data "aws_iam_policy_document" "task" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.app.arn, var.database_secret_arn]
  }

  statement {
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = local.bedrock_resources
  }

  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.sandbox.arn]
  }

  #checkov:skip=CKV_AWS_111:ssmmessages has no resource-level permissions
  #checkov:skip=CKV_AWS_356:ssmmessages has no resource-level permissions
  statement {
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "task" {
  name   = "${local.app_name}-task"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task.json
}

# IAM role declaration for ECS itself, which moves the listener rule weights during a canary deployment
data "aws_iam_policy_document" "ecs_infrastructure_assume_role" {
  count = local.canary ? 1 : 0

  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_infrastructure" {
  count = local.canary ? 1 : 0

  name                 = "${var.name}-ecs-infrastructure"
  assume_role_policy   = data.aws_iam_policy_document.ecs_infrastructure_assume_role[0].json
  permissions_boundary = var.permissions_boundary_arn
}

resource "aws_iam_role_policy_attachment" "ecs_infrastructure" {
  count = local.canary ? 1 : 0

  role       = aws_iam_role.ecs_infrastructure[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECSInfrastructureRolePolicyForLoadBalancers"
}
