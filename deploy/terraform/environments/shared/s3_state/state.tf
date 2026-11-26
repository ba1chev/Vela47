provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}

# The bucket this root module creates does not exist on the first apply. deploy/bootstrap.sh applies it once with a
# local backend (a temporary backend_override.tf) and then moves the state into the bucket it just created
terraform {
  backend "s3" {
    bucket       = "vela47-terraform-state"
    key          = "shared/s3_state/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
