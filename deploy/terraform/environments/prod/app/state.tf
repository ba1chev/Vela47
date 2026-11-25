provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}

# Docker builds the two images on this machine and pushes them to ECR with a short-lived token
# Docker Desktop on a Mac has no /var/run/docker.sock, the provider reaches it through its context
data "aws_ecr_authorization_token" "this" {}

provider "docker" {
  context = var.docker_context

  registry_auth {
    address  = replace(data.aws_ecr_authorization_token.this.proxy_endpoint, "https://", "")
    username = data.aws_ecr_authorization_token.this.user_name
    password = data.aws_ecr_authorization_token.this.password
  }
}

terraform {
  backend "s3" {
    bucket       = "vela47-terraform-state"
    key          = "prod/app/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
