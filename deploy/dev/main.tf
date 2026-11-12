# The local development deployment: the Vela47 server and its PostgreSQL, each in its own
# container on its own network. The server is published on 127.0.0.1:8000, reaches Ollama on
# the host through host.docker.internal and starts the sandbox project through the host's
# Docker socket, so the sandbox containers run next to it, not inside it.
#
# No container sits on both networks. The server reaches the database at its address on the
# database network: the packets leave through the app network's gateway and enter through
# the database network's gateway. Docker forwards between the two only to a published port,
# so 5432 is published, on 127.0.0.1, which keeps it off the LAN. Every other port of the
# database container stays unreachable from the app network, and the sandbox network, whose
# gateway is isolated, reaches none of them.

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

provider "docker" {
  context = var.docker_context
}

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

resource "random_password" "token_secret" {
  length  = 48
  special = false
}

resource "random_password" "admin_password" {
  length  = 24
  special = false
}

resource "random_password" "database_password" {
  length  = 32
  special = false
}

resource "docker_network" "database" {
  name   = "vela47-db-network"
  driver = "bridge"

  ipam_config {
    subnet  = var.database_network_subnet
    gateway = var.database_network_gateway
  }
}

resource "docker_network" "app" {
  name   = "vela47-app-network"
  driver = "bridge"

  ipam_config {
    subnet  = var.application_network_subnet
    gateway = var.application_network_gateway
  }
}

resource "docker_image" "database" {
  name = "vela47-db:dev"

  build {
    context = local.database_context
  }

  triggers = {
    dockerfile_sha1 = filesha1("${local.database_context}/Dockerfile")
  }
}

resource "docker_volume" "database" {
  name = "vela47-db-data"
}

resource "docker_container" "database" {
  name  = "vela47-db"
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
    ip       = "127.0.0.1"
  }

  volumes {
    volume_name    = docker_volume.database.name
    container_path = "/var/lib/postgresql/data"
  }

  healthcheck {
    test         = ["CMD", "pg_isready", "--host", "127.0.0.1", "--username", "vela47", "--dbname", "vela47"]
    interval     = "2s"
    timeout      = "5s"
    retries      = 3
    start_period = "1m"
  }

  wait                  = true
  wait_timeout          = 120
  stop_timeout          = 30
  destroy_grace_seconds = 30
}

resource "docker_image" "app" {
  name = "vela47-app:dev"

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

resource "docker_container" "app" {
  name       = "vela47-app"
  image      = docker_image.app.image_id
  init       = true
  depends_on = [docker_container.database]

  env = [
    "VELA47_ENVIRONMENT=dev",
    "VELA47_DATABASE_HOST=${var.database_container_address}",
    "VELA47_DATABASE_SSL_MODE=disable",
    "VELA47_DATABASE_USERNAME=vela47",
    "VELA47_DATABASE_PASSWORD=${random_password.database_password.result}",
    "VELA47_TOKEN_SECRET=${random_password.token_secret.result}",
    "VELA47_ADMIN_USERNAME=${var.admin_username}",
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
    ip       = "127.0.0.1"
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
    interval     = "5s"
    timeout      = "5s"
    retries      = 3
    start_period = "5m"
  }

  wait                  = true
  wait_timeout          = 600
  stop_timeout          = 60
  destroy_grace_seconds = 60
}
