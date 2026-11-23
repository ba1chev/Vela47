terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.9.1"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Docker builds the two images on this machine and pushes them to ECR with a short-lived token
# Docker Desktop on a Mac has no /var/run/docker.sock, the provider reaches it through its context
data "aws_ecr_authorization_token" "main" {}

provider "docker" {
  context = var.docker_context

  registry_auth {
    address  = replace(data.aws_ecr_authorization_token.main.proxy_endpoint, "https://", "")
    username = data.aws_ecr_authorization_token.main.user_name
    password = data.aws_ecr_authorization_token.main.password
  }
}
