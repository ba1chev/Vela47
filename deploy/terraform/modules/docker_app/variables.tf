# General variables
variable "name" {
  description = "Prefix of the name of the network, image and container"
  type        = string
}

variable "repository_path" {
  description = "Absolute path of the repository root, the context the server image is built from"
  type        = string
}

variable "dockerfile" {
  description = "Dockerfile of the server image, relative to repository_path"
  type        = string
  default     = "deploy/images/dev/app/Dockerfile"
}

variable "sandbox_directory" {
  description = "Sandbox compose project copied into the server image, relative to repository_path"
  type        = string
  default     = "deploy/images/dev/sandbox"
}

variable "ollama_host" {
  description = "URL of the Ollama server on the host, as the container reaches it"
  type        = string
}

# Network and container variables
variable "network_subnet" {
  description = "Subnet of the application network"
  type        = string

  validation {
    condition     = can(cidrhost(var.network_subnet, 0))
    error_message = "The network_subnet must be a valid IPv4 CIDR, e.g. 10.112.0.0/16."
  }
}

variable "network_gateway" {
  description = "Gateway of the application network"
  type        = string
}

variable "container_address" {
  description = "Address of the application container on its network"
  type        = string
}

variable "published_address" {
  description = "Host address the server and its UI are published on, 127.0.0.1 keeps them off the LAN"
  type        = string
}

variable "published_port" {
  description = "Port the server and its UI are published on"
  type        = number

  validation {
    condition     = var.published_port >= 1 && var.published_port <= 65535
    error_message = "The published port must be between 1 and 65535."
  }
}

variable "health_check_interval" {
  description = "Time between two health checks of the container"
  type        = string
  default     = "5s"
}

variable "health_check_timeout" {
  description = "Time one health check of the container may take"
  type        = string
  default     = "5s"
}

variable "health_check_retries" {
  description = "Failed health checks in a row after which the container is unhealthy"
  type        = number
  default     = 3
}

variable "health_check_start_period" {
  description = "Time the server gets to start, including bringing up the sandbox, before failed health checks count"
  type        = string
  default     = "5m"
}

variable "wait_timeout" {
  description = "Seconds Terraform waits for the container to become healthy"
  type        = number
  default     = 600
}

variable "stop_timeout" {
  description = "Seconds the server gets to bring the sandbox down when its container is stopped or destroyed"
  type        = number
  default     = 60
}

# Database variables (outputs of the docker_database module)
variable "database_host" {
  description = "Address of the database container, VELA47_DATABASE_HOST"
  type        = string
}

variable "database_password" {
  description = "Password of the vela47 user on the database, VELA47_DATABASE_PASSWORD"
  type        = string
  sensitive   = true
}

# Server secrets variables (token signing key and the admin bootstrapped on the first start)
variable "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  type        = string
}

variable "token_secret_length" {
  description = "Length of the key which signs the session tokens"
  type        = number
  default     = 48

  validation {
    condition     = var.token_secret_length >= 32
    error_message = "The server needs a token secret of at least 32 characters."
  }
}

variable "admin_password_length" {
  description = "Length of the password of the admin bootstrapped on the first start"
  type        = number
  default     = 24

  validation {
    condition     = var.admin_password_length >= 12
    error_message = "The server needs an admin password of at least 12 characters."
  }
}
