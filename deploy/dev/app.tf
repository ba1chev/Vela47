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
