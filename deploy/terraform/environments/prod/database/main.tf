# The VPC and its subnets, outputs of the vpc root module
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = var.state_bucket
    key    = "prod/vpc/eu-central-1/terraform.tfstate"
    region = var.region
  }
}

module "database" {
  source = "../../../modules/database"

  name                    = var.name
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  subnet_ids              = data.terraform_remote_state.vpc.outputs.private_subnet_ids
  instance_class          = var.instance_class
  multi_az                = var.multi_az
  backup_retention_period = var.backup_retention_period
  skip_final_snapshot     = var.skip_final_snapshot
  deletion_protection     = var.deletion_protection
}
