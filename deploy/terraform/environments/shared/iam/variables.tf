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
  description = "Project name every resource of the AWS environments starts with"
  type        = string
  default     = "vela47"
}

variable "ci_role_name" {
  description = "Role GitHub Actions assumes through OpenID Connect, created by hand (see docs/open_id_connect.md)"
  type        = string
  default     = "vela47-role"
}

variable "environments" {
  description = "AWS environments the pipeline deploys"
  type        = list(string)
  default     = ["dev", "staging", "prod"]
}

variable "state_bucket" {
  description = "Bucket of the Terraform state"
  type        = string
  default     = "vela47-terraform-state"
}

variable "artifacts_bucket" {
  description = "Bucket of the releases and the deployment records"
  type        = string
  default     = "vela47-artifacts"
}

variable "instance_types" {
  description = "The only EC2 instance types the pipeline may launch: the NAT instance of dev and the cluster instances"
  type        = list(string)
  default     = ["t4g.nano", "t4g.small", "t4g.medium"]
}
