# General variables
variable "docker_context" {
  type        = string
  default     = "desktop-linux"
  description = "Docker context the provider talks to, Docker Desktop on a Mac has no /var/run/docker.sock"
}

variable "docker_network_driver" {
  type        = string
  default     = "bridge"
  description = "Driver of the database and application networks"
}

variable "published_address" {
  type        = string
  default     = "127.0.0.1"
  description = "Host address the server and PostgreSQL are published on, 127.0.0.1 keeps them off the LAN"

  validation {
    condition     = can(cidrhost("${var.published_address}/32", 0))
    error_message = "The published address must be an IPv4 address, e.g. 127.0.0.1."
  }
}

variable "ollama_host" {
  type        = string
  default     = "http://host.docker.internal:11434"
  description = "URL of the Ollama server on the host, as the application container reaches it"
}

# Database network and container variables
variable "database_network_name" {
  type        = string
  default     = "vela47-db-network"
  description = "Name for the database container network"
}

variable "database_network_subnet" {
  type        = string
  default     = "10.111.0.0/16"
  description = "Value for the database container network subnet"

  validation {
    condition     = can(cidrhost(var.database_network_subnet, 0))
    error_message = "The database_network_subnet must be a valid IPv4 CIDR, e.g. 10.111.0.0/16."
  }
}

variable "database_network_gateway" {
  type        = string
  default     = "10.111.0.1"
  description = "Value for the database container network gateway"
}

variable "database_image_name" {
  type        = string
  default     = "vela47-db:dev"
  description = "Name and tag for the database image"
}

variable "database_volume_name" {
  type        = string
  default     = "vela47-db-data"
  description = "Name for the volume which holds the PostgreSQL data"
}

variable "database_container_name" {
  type        = string
  default     = "vela47-db"
  description = "Name for the database container"
}

variable "database_container_address" {
  type        = string
  default     = "10.111.0.2"
  description = "Address of the database container on its network, the server connects to it"
}

variable "database_published_port" {
  type        = number
  default     = 5432
  description = "Port PostgreSQL is published on, the server still connects to the container's 5432"

  validation {
    condition     = var.database_published_port >= 1 && var.database_published_port <= 65535
    error_message = "The database published port must be between 1 and 65535."
  }
}

variable "database_password_length" {
  type        = number
  default     = 32
  description = "Length of the password of the vela47 user on PostgreSQL"
}

variable "database_health_check_interval" {
  type        = string
  default     = "2s"
  description = "Time between two health checks of the database container"
}

variable "database_health_check_timeout" {
  type        = string
  default     = "5s"
  description = "Time one health check of the database container may take"
}

variable "database_health_check_retries" {
  type        = number
  default     = 3
  description = "Failed health checks in a row after which the database container is unhealthy"
}

variable "database_health_check_start_period" {
  type        = string
  default     = "1m"
  description = "Time PostgreSQL gets to start before failed health checks count"
}

variable "database_wait_timeout" {
  type        = number
  default     = 120
  description = "Seconds Terraform waits for the database container to become healthy"
}

variable "database_stop_timeout" {
  type        = number
  default     = 30
  description = "Seconds PostgreSQL gets to shut down when its container is stopped or destroyed"
}

# Application network and container variables
variable "application_network_name" {
  type        = string
  default     = "vela47-app-network"
  description = "Name for the application container network"
}

variable "application_network_subnet" {
  type        = string
  default     = "10.112.0.0/16"
  description = "Value for the application container network subnet"

  validation {
    condition     = can(cidrhost(var.application_network_subnet, 0))
    error_message = "The application_network_subnet must be a valid IPv4 CIDR, e.g. 10.112.0.0/16."
  }
}

variable "application_network_gateway" {
  type        = string
  default     = "10.112.0.1"
  description = "Value for the application container network gateway"
}

variable "application_image_name" {
  type        = string
  default     = "vela47-app:dev"
  description = "Name and tag for the server image"
}

variable "application_container_name" {
  type        = string
  default     = "vela47-app"
  description = "Name for the application container"
}

variable "application_container_address" {
  type        = string
  default     = "10.112.0.2"
  description = "Address of the application container on its network"
}

variable "application_published_port" {
  type        = number
  default     = 8000
  description = "Port the server and its UI are published on"

  validation {
    condition     = var.application_published_port >= 1 && var.application_published_port <= 65535
    error_message = "The application published port must be between 1 and 65535."
  }
}

variable "application_health_check_interval" {
  type        = string
  default     = "5s"
  description = "Time between two health checks of the application container"
}

variable "application_health_check_timeout" {
  type        = string
  default     = "5s"
  description = "Time one health check of the application container may take"
}

variable "application_health_check_retries" {
  type        = number
  default     = 3
  description = "Failed health checks in a row after which the application container is unhealthy"
}

variable "application_health_check_start_period" {
  type        = string
  default     = "5m"
  description = "Time the server gets to start, including bringing up the sandbox, before failed health checks count"
}

variable "application_wait_timeout" {
  type        = number
  default     = 600
  description = "Seconds Terraform waits for the application container to become healthy"
}

variable "application_stop_timeout" {
  type        = number
  default     = 60
  description = "Seconds the server gets to bring the sandbox down when its container is stopped or destroyed"
}

# Server secrets variables (token signing key and the admin bootstrapped on the first start)
variable "app_token_secret_length" {
  type        = number
  default     = 48
  description = "Length of the key which signs the session tokens"

  validation {
    condition     = var.app_token_secret_length >= 32
    error_message = "The server needs a token secret of at least 32 characters."
  }
}

variable "app_admin_username" {
  type        = string
  default     = "admin"
  description = "Username of the admin bootstrapped on the first start"
}

variable "app_admin_password_length" {
  type        = number
  default     = 24
  description = "Length of the password of the admin bootstrapped on the first start"

  validation {
    condition     = var.app_admin_password_length >= 12
    error_message = "The server needs an admin password of at least 12 characters."
  }
}
