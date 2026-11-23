terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.9.1"
    }
  }
}

# Docker Desktop on a Mac has no /var/run/docker.sock, the provider reaches it through its context
provider "docker" {
  context = var.docker_context
}
