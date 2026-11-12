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

# Paths of the images, and the files whose change rebuilds the server image
locals {
  repository       = abspath("${path.module}/../..")
  app_dockerfile   = "deploy/dev/images/app_image/Dockerfile"
  database_context = "${local.repository}/deploy/dev/images/db_image"
  source_files = sort([
    for current_file in setunion(
      fileset(local.repository, "app/**"),
      fileset(local.repository, "db/**"),
      fileset(local.repository, "deploy/dev/images/sandbox_image/**"),
      ["requirements.txt", local.app_dockerfile]
    ) : current_file if !strcontains(current_file, "__pycache__") && !strcontains(current_file, ".sqlite3")
  ])
}

# Passwords declaration (kept in the Terraform state, read them with terraform output)
resource "random_password" "token_secret" {
  length  = var.app_token_secret_length
  special = false
}

resource "random_password" "admin_password" {
  length  = var.app_admin_password_length
  special = false
}

resource "random_password" "database_password" {
  length  = var.database_password_length
  special = false
}

# Networks declaration (the server and the database each on its own network, no container is on both)
# The server reaches the database at its address on the database network: the packets leave through
# the application network gateway and enter through the database network gateway
resource "docker_network" "database" {
  name   = var.database_network_name
  driver = var.docker_network_driver

  ipam_config {
    subnet  = var.database_network_subnet
    gateway = var.database_network_gateway
  }
}

resource "docker_network" "app" {
  name   = var.application_network_name
  driver = var.docker_network_driver

  ipam_config {
    subnet  = var.application_network_subnet
    gateway = var.application_network_gateway
  }
}

# Database image declaration (PostgreSQL in place of RDS, rebuilt when its Dockerfile changes)
resource "docker_image" "database" {
  name = var.database_image_name

  build {
    context = local.database_context
  }

  triggers = {
    dockerfile_sha1 = filesha1("${local.database_context}/Dockerfile")
  }
}

# Database volume declaration (survives a rebuild of the container, terraform destroy deletes it)
resource "docker_volume" "database" {
  name = var.database_volume_name
}

# Database container declaration
# Docker forwards between two bridge networks only to a published port, so 5432 is published, on the
# published address which keeps it off the LAN. Every other port stays unreachable from the application
# network, and the sandbox network, whose gateway is isolated, reaches none of them
resource "docker_container" "database" {
  name  = var.database_container_name
  image = docker_image.database.image_id

  env = [
    "POSTGRES_PASSWORD=${random_password.database_password.result}",
  ]

  networks_advanced {
    name         = docker_network.database.name
    ipv4_address = var.database_container_address
  }

  ports {
    internal = 5432
    external = var.database_published_port
    ip       = var.published_address
  }

  volumes {
    volume_name    = docker_volume.database.name
    container_path = "/var/lib/postgresql/data"
  }

  # The user and the database vela47 are fixed by the database image
  healthcheck {
    test         = ["CMD", "pg_isready", "--host", "127.0.0.1", "--username", "vela47", "--dbname", "vela47"]
    interval     = var.database_health_check_interval
    timeout      = var.database_health_check_timeout
    retries      = var.database_health_check_retries
    start_period = var.database_health_check_start_period
  }

  wait                  = true
  wait_timeout          = var.database_wait_timeout
  stop_timeout          = var.database_stop_timeout
  destroy_grace_seconds = var.database_stop_timeout
}

# Server image declaration (built from the repository root, rebuilt when a file it is built from changes)
resource "docker_image" "app" {
  name = var.application_image_name

  build {
    context    = local.repository
    dockerfile = local.app_dockerfile
  }

  triggers = {
    source_sha1 = sha1(join("", [
      for current_file in local.source_files : filesha1("${local.repository}/${current_file}")
    ]))
  }
}

# Server container declaration
# It reaches Ollama on the host through host.docker.internal and brings the sandbox project up through
# the host's Docker socket, so the sandbox containers run next to it, not inside it
resource "docker_container" "app" {
  name       = var.application_container_name
  image      = docker_image.app.image_id
  init       = true
  depends_on = [docker_container.database]

  # The database image has no SSL, and its user vela47 is fixed there
  env = [
    "VELA47_ENVIRONMENT=dev",
    "VELA47_DATABASE_HOST=${var.database_container_address}",
    "VELA47_DATABASE_SSL_MODE=disable",
    "VELA47_DATABASE_USERNAME=vela47",
    "VELA47_DATABASE_PASSWORD=${random_password.database_password.result}",
    "VELA47_TOKEN_SECRET=${random_password.token_secret.result}",
    "VELA47_ADMIN_USERNAME=${var.app_admin_username}",
    "VELA47_ADMIN_PASSWORD=${random_password.admin_password.result}",
    "OLLAMA_HOST=${var.ollama_host}",
  ]

  networks_advanced {
    name         = docker_network.app.name
    ipv4_address = var.application_container_address
  }

  ports {
    internal = 8000
    external = var.application_published_port
    ip       = var.published_address
  }

  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  volumes {
    host_path      = "/var/run/docker.sock"
    container_path = "/var/run/docker.sock"
  }

  healthcheck {
    test         = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout = 5)"]
    interval     = var.application_health_check_interval
    timeout      = var.application_health_check_timeout
    retries      = var.application_health_check_retries
    start_period = var.application_health_check_start_period
  }

  wait                  = true
  wait_timeout          = var.application_wait_timeout
  stop_timeout          = var.application_stop_timeout
  destroy_grace_seconds = var.application_stop_timeout
}
