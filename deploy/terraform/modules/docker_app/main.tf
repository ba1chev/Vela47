# Names of the resources, and the files whose change rebuilds the server image
locals {
  name = "${var.name}-app"
  source_files = sort([
    for current_file in setunion(
      fileset(var.repository_path, "app/**"),
      fileset(var.repository_path, "db/**"),
      fileset(var.repository_path, "${var.sandbox_directory}/**"),
      ["requirements.txt", var.dockerfile]
    ) : current_file if !strcontains(current_file, "__pycache__") && !strcontains(current_file, ".sqlite3")
  ])
}

# Network declaration (the server on a network of its own, no other container is on it)
# The server reaches the database at its address on the database network: the packets leave through
# this network's gateway and enter through the database network's gateway
resource "docker_network" "this" {
  name   = "${local.name}-network"
  driver = "bridge"

  ipam_config {
    subnet  = var.network_subnet
    gateway = var.network_gateway
  }
}

# Image declaration (built from the repository root, rebuilt when a file it is built from changes)
resource "docker_image" "this" {
  name = "${local.name}:local"

  build {
    context    = var.repository_path
    dockerfile = var.dockerfile
  }

  triggers = {
    source_sha1 = sha1(join("", [
      for current_file in local.source_files : filesha1("${var.repository_path}/${current_file}")
    ]))
  }
}

# Secret declarations (kept in the Terraform state, read them with terraform output)
resource "random_password" "token_secret" {
  length  = var.token_secret_length
  special = false
}

resource "random_password" "admin_password" {
  length  = var.admin_password_length
  special = false
}

# Container declaration
# It reaches Ollama on the host through host.docker.internal and brings the sandbox project up through
# the host's Docker socket, so the sandbox containers run next to it, not inside it
resource "docker_container" "this" {
  name  = local.name
  image = docker_image.this.image_id
  init  = true

  # The database image has no SSL, and its user vela47 is fixed there
  env = [
    "VELA47_ENVIRONMENT=local",
    "VELA47_DATABASE_HOST=${var.database_host}",
    "VELA47_DATABASE_SSL_MODE=disable",
    "VELA47_DATABASE_USERNAME=vela47",
    "VELA47_DATABASE_PASSWORD=${var.database_password}",
    "VELA47_TOKEN_SECRET=${random_password.token_secret.result}",
    "VELA47_ADMIN_USERNAME=${var.admin_username}",
    "VELA47_ADMIN_PASSWORD=${random_password.admin_password.result}",
    "OLLAMA_HOST=${var.ollama_host}",
  ]

  networks_advanced {
    name         = docker_network.this.name
    ipv4_address = var.container_address
  }

  ports {
    internal = 8000
    external = var.published_port
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
