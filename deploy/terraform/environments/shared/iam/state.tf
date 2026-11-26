provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}

terraform {
  backend "s3" {
    bucket       = "vela47-terraform-state"
    key          = "shared/iam/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
