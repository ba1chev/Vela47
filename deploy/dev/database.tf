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
