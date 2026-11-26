variable "name" {
  description = "Project name every resource of the AWS environments starts with, the policies are scoped to it"
  type        = string
}

variable "role_name" {
  description = "Role GitHub Actions assumes through OpenID Connect, created outside Terraform"
  type        = string
}

variable "region" {
  description = "The only region the pipeline may work in"
  type        = string
}

variable "environments" {
  description = "AWS environments the pipeline deploys, each keeps its state under a prefix of its own"
  type        = list(string)
}

variable "state_bucket" {
  description = "Bucket of the Terraform state"
  type        = string
}

variable "artifacts_bucket" {
  description = "Bucket of the releases and the deployment records"
  type        = string
}

variable "instance_types" {
  description = "The only EC2 instance types the pipeline may launch"
  type        = list(string)
}
