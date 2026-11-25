provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}

### The bucket this root module creates does not exist on the first apply, so its state starts local.
### Uncomment this after the first apply and run terraform init -migrate-state to move the state into the bucket
# terraform {
#   backend "s3" {
#     bucket       = "vela47-terraform-state"
#     key          = "prod/global/s3_state/terraform.tfstate"
#     region       = "eu-central-1"
#     encrypt      = true
#     use_lockfile = true
#   }
# }
