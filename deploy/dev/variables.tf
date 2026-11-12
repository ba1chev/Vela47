variable "docker_context" {
  type        = string
  description = "Docker context the provider talks to; Docker Desktop on a Mac has no /var/run/docker.sock"
  default     = "desktop-linux"
}

variable "database_network_subnet" {
  type        = string
  description = "Value for the database container network subnet"
  default     = "10.111.0.0/16"
}

variable "database_network_gateway" {
  type        = string
  description = "Value for the database container network gateway"
  default     = "10.111.0.1"
}

variable "database_container_address" {
  type        = string
  description = "Address of the database container on its network; the server connects to it"
  default     = "10.111.0.2"
}

variable "database_published_port" {
  type        = number
  description = "Port on 127.0.0.1 that PostgreSQL is published on; the server still connects to the container's 5432"
  default     = 5432
}

variable "application_network_subnet" {
  type        = string
  description = "Value for the application container network subnet"
  default     = "10.112.0.0/16"
}

variable "application_network_gateway" {
  type        = string
  description = "Value for the application container network gateway"
  default     = "10.112.0.1"
}

variable "application_container_address" {
  type        = string
  description = "Address of the application container on its network"
  default     = "10.112.0.2"
}

variable "application_published_port" {
  type        = number
  description = "Port on 127.0.0.1 that the server and its UI are published on"
  default     = 8000
}

variable "ollama_host" {
  type        = string
  description = "URL of the Ollama server on the host, as the application container reaches it"
  default     = "http://host.docker.internal:11434"
}

variable "admin_username" {
  type        = string
  description = "Username of the admin bootstrapped on the first start"
  default     = "admin"
}
