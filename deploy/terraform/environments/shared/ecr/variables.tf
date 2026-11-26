variable "region" {
  description = "AWS region where all resources are created"
  type        = string
  default     = "eu-central-1"
}

variable "tags" {
  description = "Tags every resource of the root module gets through default_tags of the provider"
  type        = map(string)
  default = {
    owner       = "ba1chev"
    project     = "vela47"
    environment = "shared"
    created_by  = "terraform"
  }
}

variable "name" {
  description = "Prefix of the repository names"
  type        = string
  default     = "vela47"
}

variable "kept_images" {
  description = "How many release images each repository keeps, enough for every environment and a rollback"
  type        = number
  default     = 30
}
