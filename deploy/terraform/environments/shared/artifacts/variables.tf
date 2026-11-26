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

variable "artifacts_bucket" {
  description = "Bucket of the releases (releases/<version>/) and the deployment records (deployments/<environment>/)"
  type        = string
  default     = "vela47-artifacts"
}

variable "noncurrent_version_expiration_days" {
  description = "Days an overwritten deployment record is kept, the history of an environment"
  type        = number
  default     = 365
}
