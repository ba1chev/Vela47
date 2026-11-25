locals {
  repository_path = abspath("${path.module}/../../../../..")
}

module "docker_database" {
  source = "../../../modules/docker_database"

  name              = var.name
  image_context     = "${local.repository_path}/deploy/images/dev/database"
  network_subnet    = var.database_network_subnet
  network_gateway   = var.database_network_gateway
  container_address = var.database_container_address
  published_address = var.published_address
  published_port    = var.database_published_port
}

module "docker_app" {
  source = "../../../modules/docker_app"

  name              = var.name
  repository_path   = local.repository_path
  ollama_host       = var.ollama_host
  network_subnet    = var.application_network_subnet
  network_gateway   = var.application_network_gateway
  container_address = var.application_container_address
  published_address = var.published_address
  published_port    = var.application_published_port
  database_host     = module.docker_database.container_address
  database_password = module.docker_database.password
  admin_username    = var.admin_username
}
