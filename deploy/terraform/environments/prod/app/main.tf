# The VPC and its subnets, outputs of the vpc root module
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = "prod/vpc/eu-central-1/terraform.tfstate"
    region = var.region
  }
}

# The RDS instance and its security group, outputs of the database root module
data "terraform_remote_state" "database" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = "prod/database/terraform.tfstate"
    region = var.region
  }
}

module "app" {
  source = "../../../modules/app"

  name            = var.name
  region          = var.region
  repository_path = abspath("${path.module}/../../../../..")

  vpc_id             = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnet_ids  = data.terraform_remote_state.vpc.outputs.public_subnet_ids
  private_subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnet_ids

  database_address           = data.terraform_remote_state.database.outputs.db_instance_address
  database_port              = data.terraform_remote_state.database.outputs.db_instance_port
  database_name              = data.terraform_remote_state.database.outputs.db_instance_name
  database_secret_arn        = data.terraform_remote_state.database.outputs.db_instance_master_user_secret_arn
  database_security_group_id = data.terraform_remote_state.database.outputs.security_group_id

  instance_type         = var.instance_type
  zone_name             = var.zone_name
  domain_name           = var.domain_name
  admin_username        = var.admin_username
  tavily_api_key        = var.tavily_api_key
  bedrock_model_ids     = var.bedrock_model_ids
  sandbox_function_name = var.sandbox_function_name
}
