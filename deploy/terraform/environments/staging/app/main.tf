# The VPC and its subnets, outputs of the vpc root module
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = "staging/vpc/eu-central-1/terraform.tfstate"
    region = var.region
  }
}

# The RDS instance and its security group, outputs of the database root module
data "terraform_remote_state" "database" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = "staging/database/terraform.tfstate"
    region = var.region
  }
}

# The release being deployed, written by the delivery workflow: its version and the digests of its images
data "aws_s3_object" "release" {
  bucket = var.artifacts_bucket
  key    = "releases/${var.release_version}/release.yaml"
}

data "aws_caller_identity" "current" {}

locals {
  release                  = yamldecode(data.aws_s3_object.release.body)
  permissions_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/vela47-boundary"
}

module "app" {
  source = "../../../modules/app"

  name                     = var.name
  environment              = var.environment
  region                   = var.region
  permissions_boundary_arn = local.permissions_boundary_arn
  log_retention_days       = var.log_retention_days

  release_version = local.release.version
  app_image       = local.release.images.app
  sandbox_image   = local.release.images.sandbox

  vpc_id             = data.terraform_remote_state.vpc.outputs.vpc_id
  vpc_cidr_block     = data.terraform_remote_state.vpc.outputs.cidr_block
  public_subnet_ids  = data.terraform_remote_state.vpc.outputs.public_subnet_ids
  private_subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnet_ids

  database_address           = data.terraform_remote_state.database.outputs.db_instance_address
  database_port              = data.terraform_remote_state.database.outputs.db_instance_port
  database_name              = data.terraform_remote_state.database.outputs.db_instance_name
  database_secret_arn        = data.terraform_remote_state.database.outputs.db_instance_master_user_secret_arn
  database_security_group_id = data.terraform_remote_state.database.outputs.security_group_id

  instance_type       = var.instance_type
  instance_min_count  = var.instance_min_count
  instance_max_count  = var.instance_max_count
  task_desired_count  = var.task_desired_count
  deployment_strategy = var.deployment_strategy

  load_balancer_deletion_protection = var.load_balancer_deletion_protection
  secret_recovery_window_in_days    = var.secret_recovery_window_in_days

  zone_name         = var.zone_name
  domain_name       = var.domain_name
  admin_username    = var.admin_username
  tavily_api_key    = var.tavily_api_key
  bedrock_model_ids = var.bedrock_model_ids
}
