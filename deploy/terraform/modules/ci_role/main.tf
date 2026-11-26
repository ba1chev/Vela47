# The role GitHub Actions assumes through OpenID Connect already exists (see docs/open_id_connect.md); this module only
# gives it its permissions and defines the boundary every role the pipeline creates must carry
data "aws_caller_identity" "current" {}

data "aws_iam_role" "this" {
  name = var.role_name
}

locals {
  account_id    = data.aws_caller_identity.current.account_id
  boundary_name = "${var.name}-boundary"
  boundary_arn  = "arn:aws:iam::${local.account_id}:policy/${local.boundary_name}"
  project_roles = "arn:aws:iam::${local.account_id}:role/${var.name}-*"
  ci_policy_arn = "arn:aws:iam::${local.account_id}:policy/${var.name}-ci"
}

# Permissions boundary declaration: the most any role of an environment may ever do, whatever policy it is given.
# The pipeline can only create roles that carry it, so it can never create a role with more power than this
data "aws_iam_policy_document" "boundary" {
  statement {
    sid = "ServerTask"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "secretsmanager:GetSecretValue",
      "lambda:InvokeFunction",
      "ssmmessages:*",
    ]
    resources = ["*"]
  }

  statement {
    sid = "EcsInstancesAndAgents"
    actions = [
      "ecs:*",
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
      "ssm:*",
      "ec2messages:*",
      "ec2:Describe*",
      "ec2:CreateNetworkInterface",
      "ec2:DeleteNetworkInterface",
      "ec2:AssignPrivateIpAddresses",
      "ec2:UnassignPrivateIpAddresses",
      "ec2:CreateTags",
      "elasticloadbalancing:*",
      "autoscaling:*",
      "cloudwatch:PutMetricData",
      "cloudwatch:DescribeAlarms",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "Schedule"
    actions   = ["rds:StopDBInstance", "rds:StartDBInstance"]
    resources = ["*"]
  }

  statement {
    sid       = "NoIdentityChanges"
    effect    = "Deny"
    actions   = ["iam:*", "sts:AssumeRole", "organizations:*", "account:*"]
    resources = ["*"]
  }

  #checkov:skip=CKV_AWS_107:A boundary only caps the roles beneath it, their own policies name the resources
  #checkov:skip=CKV_AWS_108:A boundary only caps the roles beneath it, their own policies name the resources
  #checkov:skip=CKV_AWS_109:A boundary only caps the roles beneath it, their own policies name the resources
  #checkov:skip=CKV_AWS_110:A boundary only caps the roles beneath it, their own policies name the resources
  #checkov:skip=CKV_AWS_111:A boundary only caps the roles beneath it, their own policies name the resources
  #checkov:skip=CKV_AWS_356:A boundary only caps the roles beneath it, their own policies name the resources
}

resource "aws_iam_policy" "boundary" {
  name        = local.boundary_name
  description = "The most any role created by the Vela47 pipeline may ever be allowed"
  policy      = data.aws_iam_policy_document.boundary.json
}

# CI policy declaration: what the workflows do, and nothing about their own identity
data "aws_iam_policy_document" "ci" {
  statement {
    sid       = "StateOfTheAwsEnvironments"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [for current in var.environments : "arn:aws:s3:::${var.state_bucket}/${current}/*"]
  }

  statement {
    sid       = "ListTheBuckets"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation", "s3:GetBucketVersioning"]
    resources = ["arn:aws:s3:::${var.state_bucket}", "arn:aws:s3:::${var.artifacts_bucket}"]
  }

  statement {
    sid       = "ReleasesAndDeployments"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.artifacts_bucket}/*"]
  }

  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "EcrPushAndPull"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:GetDownloadUrlForLayer",
      "ecr:GetRepositoryPolicy",
      "ecr:InitiateLayerUpload",
      "ecr:ListImages",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = ["arn:aws:ecr:${var.region}:${local.account_id}:repository/${var.name}-*"]
  }

  statement {
    sid = "EnvironmentServices"
    actions = [
      "acm:*",
      "autoscaling:*",
      "cloudwatch:*",
      "ec2:*",
      "ecs:*",
      "elasticloadbalancing:*",
      "lambda:*",
      "logs:*",
      "rds:*",
      "scheduler:*",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.region]
    }
  }

  statement {
    sid       = "OnlySmallGravitonInstances"
    effect    = "Deny"
    actions   = ["ec2:RunInstances"]
    resources = ["arn:aws:ec2:*:*:instance/*"]

    condition {
      test     = "StringNotEquals"
      variable = "ec2:InstanceType"
      values   = var.instance_types
    }
  }

  statement {
    sid       = "AmiParameters"
    actions   = ["ssm:GetParameter", "ssm:GetParameters"]
    resources = ["arn:aws:ssm:${var.region}::parameter/aws/service/*"]
  }

  statement {
    sid       = "ApplicationSecrets"
    actions   = ["secretsmanager:*"]
    resources = ["arn:aws:secretsmanager:${var.region}:${local.account_id}:secret:${var.name}-*"]
  }

  statement {
    sid       = "Dns"
    actions   = ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets", "route53:ListTagsForResource"]
    resources = ["arn:aws:route53:::hostedzone/*"]
  }

  statement {
    sid       = "DnsLookups"
    actions   = ["route53:ListHostedZones", "route53:ListHostedZonesByName", "route53:GetChange"]
    resources = ["*"]
  }

  statement {
    sid = "ProjectRoles"
    actions = [
      "iam:GetRole",
      "iam:ListRoleTags",
      "iam:ListRolePolicies",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:GetRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:DeleteRole",
    ]
    resources = [local.project_roles]
  }

  statement {
    sid       = "ProjectRolesOnlyWithTheBoundary"
    actions   = ["iam:CreateRole", "iam:PutRolePolicy", "iam:AttachRolePolicy", "iam:PutRolePermissionsBoundary"]
    resources = [local.project_roles]

    condition {
      test     = "StringEquals"
      variable = "iam:PermissionsBoundary"
      values   = [local.boundary_arn]
    }
  }

  statement {
    sid = "ProjectInstanceProfiles"
    actions = [
      "iam:CreateInstanceProfile",
      "iam:DeleteInstanceProfile",
      "iam:GetInstanceProfile",
      "iam:ListInstanceProfileTags",
      "iam:AddRoleToInstanceProfile",
      "iam:RemoveRoleFromInstanceProfile",
      "iam:TagInstanceProfile",
    ]
    resources = ["arn:aws:iam::${local.account_id}:instance-profile/${var.name}-*"]
  }

  statement {
    sid       = "PassProjectRolesToTheirServices"
    actions   = ["iam:PassRole"]
    resources = [local.project_roles]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ec2.amazonaws.com", "ecs.amazonaws.com", "ecs-tasks.amazonaws.com", "lambda.amazonaws.com", "scheduler.amazonaws.com"]
    }
  }

  statement {
    sid       = "ReadPolicies"
    actions   = ["iam:GetPolicy", "iam:GetPolicyVersion"]
    resources = ["arn:aws:iam::aws:policy/*", local.boundary_arn]
  }

  statement {
    sid       = "ServiceLinkedRoles"
    actions   = ["iam:CreateServiceLinkedRole"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "iam:AWSServiceName"
      values   = ["autoscaling.amazonaws.com", "ecs.amazonaws.com", "elasticloadbalancing.amazonaws.com", "rds.amazonaws.com"]
    }
  }

  statement {
    sid       = "NeverItsOwnIdentity"
    effect    = "Deny"
    actions   = ["iam:*"]
    resources = [data.aws_iam_role.this.arn, local.boundary_arn, local.ci_policy_arn]
  }

  statement {
    sid       = "NeverWithoutTheBoundary"
    effect    = "Deny"
    actions   = ["iam:DeleteRolePermissionsBoundary"]
    resources = ["*"]
  }

  #checkov:skip=CKV_AWS_107:The pipeline deploys these services, they are limited to the project region
  #checkov:skip=CKV_AWS_108:The pipeline deploys these services, they are limited to the project region
  #checkov:skip=CKV_AWS_109:The pipeline deploys these services, they are limited to the project region
  #checkov:skip=CKV_AWS_110:IAM is limited to roles named after the project and only with the boundary
  #checkov:skip=CKV_AWS_111:The pipeline deploys these services, they are limited to the project region
  #checkov:skip=CKV_AWS_356:The pipeline deploys these services, they are limited to the project region
  #checkov:skip=CKV2_AWS_40:The pipeline deploys these services, they are limited to the project region
}

resource "aws_iam_policy" "ci" {
  name        = "${var.name}-ci"
  description = "What the Vela47 workflows may do in the AWS environments"
  policy      = data.aws_iam_policy_document.ci.json
}

resource "aws_iam_role_policy_attachment" "ci" {
  role       = data.aws_iam_role.this.name
  policy_arn = aws_iam_policy.ci.arn
}
