# Names of the resources, all derived from var.name
locals {
  name = "${var.name}-db"
}

# Network declaration (the database on a network of its own, no other container is on it)
resource "docker_network" "this" {
  name   = "${local.name}-network"
  driver = "bridge"

  ipam_config {
    subnet  = var.network_subnet
    gateway = var.network_gateway
  }
}

# Image declaration (PostgreSQL in place of RDS, rebuilt when its Dockerfile changes)
resource "docker_image" "this" {
  name = "${local.name}:dev"

  build {
    context = var.image_context
  }

  triggers = {
    dockerfile_sha1 = filesha1("${var.image_context}/Dockerfile")
  }
}

# Volume declaration (survives a rebuild of the container, terraform destroy deletes it)
resource "docker_volume" "this" {
  name = "${local.name}-data"
}

# Password declaration (kept in the Terraform state, read it with terraform output)
resource "random_password" "this" {
  length  = var.password_length
  special = false
}

# Container declaration
# Docker forwards between two bridge networks only to a published port, so 5432 is published, on the
# published address which keeps it off the LAN. Every other port stays unreachable from other networks,
# and the sandbox network, whose gateway is isolated, reaches none of them
resource "docker_container" "this" {
  name  = local.name
  image = docker_image.this.image_id

  env = [
    "POSTGRES_PASSWORD=${random_password.this.result}",
  ]

  networks_advanced {
    name         = docker_network.this.name
    ipv4_address = var.container_address
  }

  ports {
    internal = 5432
    external = var.published_port
    ip       = var.published_address
  }

  volumes {
    volume_name    = docker_volume.this.name
    container_path = "/var/lib/postgresql/data"
  }

  # The user and the database vela47 are fixed by the database image
  healthcheck {
    test         = ["CMD", "pg_isready", "--host", "127.0.0.1", "--username", "vela47", "--dbname", "vela47"]
    interval     = var.health_check_interval
    timeout      = var.health_check_timeout
    retries      = var.health_check_retries
    start_period = var.health_check_start_period
  }

  wait                  = true
  wait_timeout          = var.wait_timeout
  stop_timeout          = var.stop_timeout
  destroy_grace_seconds = var.stop_timeout
}
