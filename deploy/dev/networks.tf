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
