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
    environment = "staging"
    created_by  = "terraform"
  }
}

variable "name" {
  description = "Prefix of the name of every resource of the application"
  type        = string
  default     = "vela47-staging"
}

variable "state_bucket" {
  description = "Bucket of the Terraform state, created by shared/s3_state"
  type        = string
  default     = "vela47-terraform-state"
}

variable "artifacts_bucket" {
  description = "Bucket of the releases, created by shared/artifacts"
  type        = string
  default     = "vela47-artifacts"
}

variable "environment" {
  description = "Environment the server runs as, VELA47_ENVIRONMENT"
  type        = string
  default     = "staging"
}

variable "release_version" {
  description = "Version of the release to deploy, its release.yaml in the artifacts bucket names the images. Set by the deployment workflow, or with -var release_version=<version>"
  type        = string
}

variable "instance_type" {
  description = "Type of the EC2 instances, a Graviton type that fits two server tasks"
  type        = string
  default     = "t4g.medium"
}

variable "instance_min_count" {
  description = "Fewest EC2 instances the capacity provider may scale to"
  type        = number
  default     = 2
}

variable "instance_max_count" {
  description = "Most EC2 instances the capacity provider may scale to"
  type        = number
  default     = 4
}

variable "task_desired_count" {
  description = "Number of server tasks running"
  type        = number
  default     = 2
}

variable "deployment_strategy" {
  description = "How a new release replaces the running tasks, ROLLING or CANARY"
  type        = string
  default     = "CANARY"
}

variable "log_retention_days" {
  description = "Days the logs of the server tasks and the sandbox function are kept"
  type        = number
  default     = 30
}

variable "load_balancer_deletion_protection" {
  description = "Protects the load balancer from deletion"
  type        = bool
  default     = true
}

variable "secret_recovery_window_in_days" {
  description = "Days a deleted application secret can still be restored, 0 deletes it at once"
  type        = number
  default     = 7
}

variable "zone_name" {
  description = "Route 53 hosted zone which already exists in the account and holds the application domain"
  type        = string
  default     = "y47.sevc.link"
}

variable "domain_name" {
  description = "Domain the application is served on over HTTPS"
  type        = string
  default     = "vela47-staging.y47.sevc.link"
}

variable "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  type        = string
  default     = "admin"
}

variable "tavily_api_key" {
  description = "Key of the Tavily search API the server searches the web with, empty falls back to DuckDuckGo. The deployment workflow sets it from the TAVILY_API_KEY secret of the GitHub environment"
  type        = string
  default     = ""
  sensitive   = true
}

variable "bedrock_model_ids" {
  description = "Bedrock models the server task may call, the same IDs the server asks for on AWS, an eu. prefix is a cross-region inference profile that keeps the requests in EU regions"
  type        = list(string)
  default     = ["eu.anthropic.claude-sonnet-5-5", "amazon.titan-embed-text-v2:0"]
}
