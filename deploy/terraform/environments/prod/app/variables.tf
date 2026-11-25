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
    environment = "production"
    created_by  = "terraform"
  }
}

variable "state_bucket" {
  description = "Bucket of the Terraform state of the environment, created by global/s3_state"
  type        = string
  default     = "vela47-terraform-state"
}

variable "name" {
  description = "Prefix of the name of every resource of the application"
  type        = string
  default     = "vela47"
}

variable "instance_type" {
  description = "Type of the EC2 instance, t4g.medium has 2 Graviton vCPUs and 4 GB, room for the server task and a second one during a deploy"
  type        = string
  default     = "t4g.medium"
}

variable "zone_name" {
  description = "Route 53 hosted zone which already exists in the account and holds the application domain"
  type        = string
  default     = "y47.sevc.link"
}

variable "domain_name" {
  description = "Domain the application is served on over HTTPS"
  type        = string
  default     = "vela47.y47.sevc.link"
}

variable "admin_username" {
  description = "Username of the admin bootstrapped on the first start"
  type        = string
  default     = "admin"
}

variable "tavily_api_key" {
  description = "Key of the Tavily search API the server searches the web with, empty falls back to DuckDuckGo, set it with TF_VAR_tavily_api_key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "bedrock_model_ids" {
  description = "Bedrock models the server task may call, the same IDs the server asks for in PROD, an eu. prefix is a cross-region inference profile that keeps the requests in EU regions"
  type        = list(string)
  default     = ["eu.anthropic.claude-sonnet-5-5", "amazon.titan-embed-text-v2:0"]
}

variable "sandbox_function_name" {
  description = "Name of the Lambda function the TEST subagent runs its commands in, the same name the server calls"
  type        = string
  default     = "vela47-sandbox"
}

variable "docker_context" {
  description = "Docker context Terraform builds the images with, Docker Desktop on a Mac has no /var/run/docker.sock"
  type        = string
  default     = "desktop-linux"
}
