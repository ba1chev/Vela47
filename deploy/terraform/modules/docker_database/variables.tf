variable "name" {
  description = "Prefix of the name of the network, image, volume and container"
  type        = string
}

variable "image_context" {
  description = "Absolute path of the directory the database image is built from"
  type        = string
}

variable "network_subnet" {
  description = "Subnet of the database network"
  type        = string

  validation {
    condition     = can(cidrhost(var.network_subnet, 0))
    error_message = "The network_subnet must be a valid IPv4 CIDR, e.g. 10.111.0.0/16."
  }
}

variable "network_gateway" {
  description = "Gateway of the database network, clients on other networks reach the database through it"
  type        = string
}

variable "container_address" {
  description = "Address of the database container on its network, the server connects to it"
  type        = string
}

variable "published_address" {
  description = "Host address PostgreSQL is published on, 127.0.0.1 keeps it off the LAN"
  type        = string
}

variable "published_port" {
  description = "Port PostgreSQL is published on, clients still connect to the container's 5432"
  type        = number

  validation {
    condition     = var.published_port >= 1 && var.published_port <= 65535
    error_message = "The published port must be between 1 and 65535."
  }
}

variable "password_length" {
  description = "Length of the password of the vela47 user on PostgreSQL"
  type        = number
  default     = 32
}

variable "health_check_interval" {
  description = "Time between two health checks of the container"
  type        = string
  default     = "2s"
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
  description = "Time PostgreSQL gets to start before failed health checks count"
  type        = string
  default     = "1m"
}

variable "wait_timeout" {
  description = "Seconds Terraform waits for the container to become healthy"
  type        = number
  default     = 120
}

variable "stop_timeout" {
  description = "Seconds PostgreSQL gets to shut down when its container is stopped or destroyed"
  type        = number
  default     = 30
}
