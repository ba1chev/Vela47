# General variables
variable "docker_context" {
  description = "Docker context the provider talks to, Docker Desktop on a Mac has no /var/run/docker.sock"
  type        = string
  default     = "desktop-linux"
}

variable "name" {
  description = "Prefix of the name of every network, image, volume and container"
  type        = string
  default     = "vela47"
}

variable "published_address" {
  description = "Host address the server and PostgreSQL are published on, 127.0.0.1 keeps them off the LAN"
  type        = string
  default     = "127.0.0.1"

  validation {
    condition     = can(cidrhost("${var.published_address}/32", 0))
    error_message = "The published address must be an IPv4 address, e.g. 127.0.0.1."
  }
}

variable "model_client" {
  description = "Backend the models are served by, ollama on the host or bedrock with the models of the AWS environments"
  type        = string
  default     = "ollama"

  validation {
    condition     = contains(["ollama", "bedrock"], var.model_client)
    error_message = "The model client must be ollama or bedrock."
  }
}

variable "ollama_host" {
  description = "URL of the Ollama server on the host, as the application container reaches it, used with ollama"
  type        = string
  default     = "http://host.docker.internal:11434"
}

variable "aws_profile" {
  description = "Profile in the host's ~/.aws the server calls Bedrock with, used with bedrock"
  type        = string
  default     = "default"
}

variable "aws_region" {
  description = "Region the server calls Bedrock in, used with bedrock, the eu. inference profiles need an EU region"
  type        = string
  default     = "eu-central-1"
}

variable "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  type        = string
  default     = "admin"
}

# Database network and container variables
variable "database_network_subnet" {
  description = "Subnet of the database network"
  type        = string
  default     = "10.111.0.0/16"
}

variable "database_network_gateway" {
  description = "Gateway of the database network"
  type        = string
  default     = "10.111.0.1"
}

variable "database_container_address" {
  description = "Address of the database container on its network, the server connects to it"
  type        = string
  default     = "10.111.0.2"
}

variable "database_published_port" {
  description = "Port PostgreSQL is published on, the server still connects to the container's 5432"
  type        = number
  default     = 5432
}

# Application network and container variables
variable "application_network_subnet" {
  description = "Subnet of the application network"
  type        = string
  default     = "10.112.0.0/16"
}

variable "application_network_gateway" {
  description = "Gateway of the application network"
  type        = string
  default     = "10.112.0.1"
}

variable "application_container_address" {
  description = "Address of the application container on its network"
  type        = string
  default     = "10.112.0.2"
}

variable "application_published_port" {
  description = "Port the server and its UI are published on"
  type        = number
  default     = 8000
}
