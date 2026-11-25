# General variables
variable "name" {
  description = "Prefix of the name of every resource of the application"
  type        = string
}

variable "region" {
  description = "AWS region the server reads its secrets and calls the models in"
  type        = string
}

variable "repository_path" {
  description = "Absolute path of the repository root, the context the server image is built from"
  type        = string
}

variable "app_dockerfile" {
  description = "Dockerfile of the server image, relative to repository_path"
  type        = string
  default     = "deploy/images/prod/app/Dockerfile"
}

variable "sandbox_context" {
  description = "Directory the sandbox function image is built from, relative to repository_path"
  type        = string
  default     = "deploy/images/prod/sandbox"
}

variable "ecr_kept_images" {
  description = "How many images each ECR repository keeps, older ones are deleted"
  type        = number
  default     = 5
}

variable "log_retention_days" {
  description = "Days the logs of the server task and of the sandbox function are kept"
  type        = number
  default     = 14
}

# Network variables (outputs of the vpc and database root modules)
variable "vpc_id" {
  description = "VPC every resource of the application lives in"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnets of the load balancer"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnets of the EC2 instance, the server task and the sandbox function"
  type        = list(string)
}

# Database variables (outputs of the database root module)
variable "database_address" {
  description = "Host name of the RDS instance, VELA47_DATABASE_HOST"
  type        = string
}

variable "database_port" {
  description = "Port of the RDS instance, VELA47_DATABASE_PORT"
  type        = number
}

variable "database_name" {
  description = "Database on the RDS instance, VELA47_DATABASE_NAME"
  type        = string
}

variable "database_secret_arn" {
  description = "ARN of the RDS-managed secret with the database username and password, VELA47_DATABASE_SECRET_ID"
  type        = string
}

variable "database_security_group_id" {
  description = "Security group of the RDS instance, the server task adds its ingress rule to it"
  type        = string
}

# EC2 instance variables
variable "instance_ami" {
  description = "AMI of the EC2 instances, the ECS-optimized Amazon Linux 2023 for arm64 comes with Docker and the ECS agent"
  type        = string
  default     = "resolve:ssm:/aws/service/ecs/optimized-ami/amazon-linux-2023/arm64/recommended/image_id"
}

variable "instance_type" {
  description = "Type of the EC2 instances, it has to be a Graviton (arm64) type, and fit the server task and a second one during a deploy"
  type        = string
}

variable "instance_root_device_name" {
  description = "Root device name of the AMI"
  type        = string
  default     = "/dev/xvda"
}

variable "instance_root_volume_size" {
  description = "Size of the root volume in GB, it holds the image of the server task"
  type        = number
  default     = 30

  validation {
    condition     = var.instance_root_volume_size >= 30
    error_message = "The root volume can not be smaller than the 30 GB snapshot of the ECS-optimized AMI."
  }
}

variable "instance_metadata_hop_limit" {
  description = "How many network hops the instance metadata (IMDSv2) answers reach, 1 is enough since the ECS agent uses the host network and tasks get their credentials from ECS"
  type        = number
  default     = 1
}

variable "instance_min_count" {
  description = "Minimum number of EC2 instances running"
  type        = number
  default     = 1
}

variable "instance_max_count" {
  description = "Maximum number of EC2 instances running"
  type        = number
  default     = 1
}

variable "instance_desired_count" {
  description = "Desired number of EC2 instances running"
  type        = number
  default     = 1
}

variable "instance_health_check_grace_period" {
  description = "Seconds a new instance gets before failed health checks count, the ECS-optimized AMI only has to start the ECS agent"
  type        = number
  default     = 300
}

# Server task variables
variable "container_name" {
  description = "Name of the server container in the task definition"
  type        = string
  default     = "app"
}

variable "container_port" {
  description = "Port the server listens on in the container, the load balancer forwards to it"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU units the server container reserves (1024 is one vCPU)"
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Memory limit of the server container in MiB, the task is stopped beyond it"
  type        = number
  default     = 1536
}

variable "task_memory_reservation" {
  description = "Memory in MiB reserved for the server container on the instance, two tasks have to fit during a deploy"
  type        = number
  default     = 768
}

variable "task_desired_count" {
  description = "Number of server tasks running"
  type        = number
  default     = 1
}

variable "task_health_check_grace_period" {
  description = "Seconds a new server task gets before failed load balancer health checks count"
  type        = number
  default     = 60
}

# Load balancer variables
variable "load_balancer_deletion_protection" {
  description = "Protects the load balancer from deletion (true for real production)"
  type        = bool
  default     = false
}

variable "load_balancer_idle_timeout" {
  description = "Seconds a connection may stay idle, an agent run streams for minutes and an upload is embedded before it returns"
  type        = number
  default     = 300

  validation {
    condition     = var.load_balancer_idle_timeout >= 1 && var.load_balancer_idle_timeout <= 4000
    error_message = "The idle timeout must be between 1 and 4000 seconds."
  }
}

variable "load_balancer_ingress_cidr_ipv4" {
  description = "CIDR the load balancer takes HTTP and HTTPS traffic from"
  type        = string
  default     = "0.0.0.0/0"
}

variable "load_balancer_ssl_policy" {
  description = "TLS policy of the HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "load_balancer_health_check_path" {
  description = "Path the load balancer checks the server tasks on"
  type        = string
  default     = "/"
}

variable "load_balancer_deregistration_delay" {
  description = "Seconds the load balancer lets requests to a stopping task finish"
  type        = number
  default     = 30
}

# Domain variables
variable "zone_name" {
  description = "Route 53 hosted zone which already exists in the account and holds domain_name"
  type        = string
}

variable "domain_name" {
  description = "Domain the application is served on over HTTPS"
  type        = string
}

# Application secret variables
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

variable "tavily_api_key" {
  description = "Key of the Tavily search API the server searches the web with, empty falls back to DuckDuckGo"
  type        = string
  default     = ""
  sensitive   = true
}

variable "secret_recovery_window_in_days" {
  description = "Days a deleted application secret can still be restored, 0 deletes it at once so the name is free for the next apply"
  type        = number
  default     = 0

  validation {
    condition     = var.secret_recovery_window_in_days == 0 || (var.secret_recovery_window_in_days >= 7 && var.secret_recovery_window_in_days <= 30)
    error_message = "The recovery window must be 0 or between 7 and 30 days."
  }
}

# Models and sandbox variables
variable "bedrock_model_ids" {
  description = "Bedrock models the server task may call, an eu. prefix is a cross-region inference profile"
  type        = list(string)
}

variable "sandbox_function_name" {
  description = "Name of the Lambda function the TEST subagent runs its commands in, the server calls it by this name"
  type        = string
}

variable "sandbox_memory_size" {
  description = "Memory of the sandbox function in MB, the same limit a sandbox container has in development"
  type        = number
  default     = 512
}

variable "sandbox_timeout" {
  description = "Seconds the sandbox function may run, a command gets 60 and the rest is for copying the workspace in"
  type        = number
  default     = 90
}
