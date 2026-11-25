# Docker Desktop on a Mac has no /var/run/docker.sock, the provider reaches it through its context
provider "docker" {
  context = var.docker_context
}

# Development runs on this machine only, so its state stays local (terraform.tfstate, ignored by git)
