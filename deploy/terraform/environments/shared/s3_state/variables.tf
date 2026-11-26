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

variable "state_bucket" {
  description = "Bucket of the Terraform state of every root module, local excepted"
  type        = string
  default     = "vela47-terraform-state"
}
