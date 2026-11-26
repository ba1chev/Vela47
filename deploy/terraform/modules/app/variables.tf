# General variables
variable "name" {
  description = "Prefix of the name of every resource of the application, vela47-<environment>"
  type        = string
}

variable "environment" {
  description = "Environment the server runs as, VELA47_ENVIRONMENT"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment must be dev, staging or prod."
  }
}

variable "region" {
  description = "AWS region the server reads its secrets and calls the models in"
  type        = string
}

variable "permissions_boundary_arn" {
  description = "Permissions boundary of every IAM role the module creates, the most any of them may ever be allowed"
  type        = string
}

variable "log_retention_days" {
  description = "Days the logs of the server task and of the sandbox function are kept"
  type        = number
  default     = 14
}

# Release variables (from the release.yaml of the release being deployed)
variable "release_version" {
  description = "Version of the release, VELA47_VERSION, the health endpoint reports it"
  type        = string
}

variable "app_image" {
  description = "Server image of the release, an ECR URI pinned by digest"
  type        = string

  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.app_image))
    error_message = "The app_image must be pinned by digest (<repository>@sha256:<digest>)."
  }
}

variable "sandbox_image" {
  description = "Sandbox function image of the release, an ECR URI pinned by digest"
  type        = string

  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.sandbox_image))
    error_message = "The sandbox_image must be pinned by digest (<repository>@sha256:<digest>)."
  }
}

# Network variables (outputs of the vpc and database root modules)
variable "vpc_id" {
  description = "VPC every resource of the application lives in"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR of the VPC, the load balancer only sends traffic into it"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnets of the load balancer"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnets of the EC2 instances, the server tasks and the sandbox function"
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
  description = "Security group of the RDS instance, the server tasks add their ingress rule to it"
  type        = string
}

# EC2 instance variables
variable "instance_ami" {
  description = "AMI of the EC2 instances, the ECS-optimized Amazon Linux 2023 for arm64 comes with Docker and the ECS agent"
  type        = string
  default     = "resolve:ssm:/aws/service/ecs/optimized-ami/amazon-linux-2023/arm64/recommended/image_id"
}

variable "instance_type" {
  description = "Type of the EC2 instances, a Graviton (arm64) type that fits two server tasks"
  type        = string
}

variable "instance_root_device_name" {
  description = "Root device name of the AMI"
  type        = string
  default     = "/dev/xvda"
}

variable "instance_root_volume_size" {
  description = "Size of the root volume in GB, it holds the images of the server tasks"
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
  description = "Fewest EC2 instances the capacity provider may scale to, 0 lets an environment with no tasks run no instance"
  type        = number
}

variable "instance_max_count" {
  description = "Most EC2 instances the capacity provider may scale to, room for a second set of tasks during a canary deployment"
  type        = number
}

variable "instance_health_check_grace_period" {
  description = "Seconds a new instance gets before failed health checks count, the ECS-optimized AMI only has to start the ECS agent"
  type        = number
  default     = 300
}

variable "instance_max_lifetime" {
  description = "Seconds an instance may run before it is replaced by one from the newest AMI, which is how the instances get patched"
  type        = number
  default     = 1209600

  validation {
    condition     = var.instance_max_lifetime == 0 || (var.instance_max_lifetime >= 86400 && var.instance_max_lifetime <= 31536000)
    error_message = "The instance_max_lifetime must be 0 or between 86400 (a day) and 31536000 (a year) seconds."
  }
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
  description = "Memory in MiB reserved for the server container on the instance, two tasks have to fit during a deployment"
  type        = number
  default     = 768
}

variable "task_desired_count" {
  description = "Number of server tasks running"
  type        = number
}

variable "task_health_check_grace_period" {
  description = "Seconds a new server task gets before failed load balancer health checks count, it migrates the schema on start"
  type        = number
  default     = 120
}

variable "task_stop_timeout" {
  description = "Seconds a stopping server task gets to finish the answers it streams before it is killed, uvicorn gives up after 100"
  type        = number
  default     = 120
}

# Deployment variables
variable "deployment_strategy" {
  description = "How a new release replaces the running tasks: ROLLING, or CANARY through the blue and green target groups"
  type        = string

  validation {
    condition     = contains(["ROLLING", "CANARY"], var.deployment_strategy)
    error_message = "The deployment_strategy must be ROLLING or CANARY."
  }
}

variable "canary_percent" {
  description = "Share of the traffic the new tasks get first in a CANARY deployment"
  type        = number
  default     = 10
}

variable "canary_bake_time_minutes" {
  description = "Minutes a CANARY deployment watches its alarms with canary_percent of the traffic before it moves the rest"
  type        = number
  default     = 5
}

variable "bake_time_minutes" {
  description = "Minutes a CANARY deployment keeps the old tasks after all traffic moved, the window for an instant rollback and the smoke test"
  type        = number
  default     = 10
}

variable "alarm_5xx_threshold" {
  description = "Errors a minute from the server tasks that set off the 5xx alarm, two minutes in a row"
  type        = number
  default     = 5
}

# Load balancer variables
variable "load_balancer_deletion_protection" {
  description = "Protects the load balancer from deletion"
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
  default     = "/api/health"
}

variable "load_balancer_deregistration_delay" {
  description = "Seconds the load balancer lets requests to a stopping task finish, as long as the task gets to stop"
  type        = number
  default     = 120
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

variable "sandbox_memory_size" {
  description = "Memory of the sandbox function in MB, the same limit a sandbox container has locally"
  type        = number
  default     = 512
}

variable "sandbox_timeout" {
  description = "Seconds the sandbox function may run, a command gets 60 and the rest is for copying the workspace in"
  type        = number
  default     = 90
}
