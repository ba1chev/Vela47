# General variables
variable "aws_region" {
  type        = string
  default     = "eu-central-1"
  description = "AWS region where all resources are created"
}

variable "resource_name_tag" {
  type        = string
  default     = "version-1"
  description = "Value of the Name tag for the tagged resources"
}

variable "environment_tag" {
  type        = string
  default     = "production"
  description = "Value of the Environment tag for the tagged resources"
}

# VPC variables
variable "vpc_cidr_block" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR for the VPC"

  validation {
    condition     = can(cidrhost(var.vpc_cidr_block, 0))
    error_message = "The vpc_cidr_block must be a valid IPv4 CIDR, e.g. 10.0.0.0/16."
  }
}

variable "public_subnet_cidr_blocks" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDRs for the public subnets (one subnet per availability zone)"

  validation {
    condition     = length(var.public_subnet_cidr_blocks) >= 2
    error_message = "The ALB needs at least 2 public subnets in different availability zones."
  }
}

variable "private_subnet_cidr_blocks" {
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
  description = "CIDRs for the private subnets (one subnet per availability zone)"
}

# EC2 instance variables
variable "ec2_instance_ami" {
  type        = string
  default     = "resolve:ssm:/aws/service/ecs/optimized-ami/amazon-linux-2023/arm64/recommended/image_id"
  description = "EC2 instance AMI value, the ECS-optimized Amazon Linux 2023 for arm64 comes with Docker and the ECS agent"
}

variable "ec2_instance_type" {
  type        = string
  default     = "t4g.medium"
  description = "EC2 instance type value, t4g.medium has 2 Graviton vCPUs and 4 GB, room for the server task and a second one during a deploy, the models run on Bedrock and the commands in Lambda"
}

variable "ec2_instance_root_device_name" {
  type        = string
  default     = "/dev/xvda"
  description = "Root device name of the AMI"
}

variable "ec2_instance_root_volume_size" {
  type        = number
  default     = 30
  description = "Size of the root volume in GB, it holds the image of the server task"

  validation {
    condition     = var.ec2_instance_root_volume_size >= 30
    error_message = "The root volume can not be smaller than the 30 GB snapshot of the ECS-optimized AMI."
  }
}

variable "ec2_instance_egress_cidr_ipv4" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR for IPv4 for outbound traffic for the EC2 instance"
}

variable "ec2_instance_egress_ip_protocol" {
  type        = string
  default     = "-1"
  description = "IP protocol for the outbound traffic of the EC2 instance (-1 means all)"
}

variable "ec2_security_group_name" {
  type        = string
  default     = "ec2-server-instance-sg"
  description = "Name for the security group of the EC2 instance, it takes no inbound traffic, the tasks on it have security groups of their own"
}

variable "ec2_instance_metadata_hop_limit" {
  type        = number
  default     = 1
  description = "How many network hops the instance metadata (IMDSv2) answers reach, 1 is enough since the ECS agent uses the host network and tasks get their credentials from ECS"

  validation {
    condition     = var.ec2_instance_metadata_hop_limit >= 1 && var.ec2_instance_metadata_hop_limit <= 64
    error_message = "The metadata hop limit must be between 1 and 64."
  }
}

# IAM variables
variable "ec2_iam_role_name" {
  type        = string
  default     = "vela47-ec2-role"
  description = "Name for the IAM role the EC2 instances assume, it lets the ECS agent register them in the cluster"
}

variable "ec2_instance_profile_name" {
  type        = string
  default     = "vela47-ec2-instance-profile"
  description = "Name for the instance profile which hands the IAM role to the EC2 instances"
}

# Launch template and auto scaling group variables
variable "ec2_launch_template_name" {
  type        = string
  default     = "vela47-launch-template"
  description = "Name for the EC2 instances launch template"
}

variable "ec2_launch_template_min_instances" {
  type        = number
  default     = 1
  description = "Minimum number of EC2 instances running"

  validation {
    condition     = var.ec2_launch_template_min_instances >= 0
    error_message = "The minimum number of instances can not be negative."
  }
}

variable "ec2_launch_template_max_instances" {
  type        = number
  default     = 1
  description = "Maximum number of EC2 instances running"
}

variable "ec2_launch_template_desired_instances" {
  type        = number
  default     = 1
  description = "Desired number of EC2 instances running"
}

variable "ec2_autoscaling_health_check_grace_period" {
  type        = number
  default     = 300
  description = "Seconds a new instance gets before failed health checks count, the ECS-optimized AMI only has to start the ECS agent"
}

variable "ec2_autoscaling_health_check_type" {
  type        = string
  default     = "EC2"
  description = "Health check type of the auto scaling group (EC2 or ELB), EC2 since the load balancer checks the tasks rather than the instance"

  validation {
    condition     = contains(["EC2", "ELB"], var.ec2_autoscaling_health_check_type)
    error_message = "The health check type must be EC2 or ELB."
  }
}

# Load balancer variables
variable "load_balancer_name" {
  type        = string
  default     = "vela47-load-balancer"
  description = "Name for the load balancer"
}

variable "load_balancer_type" {
  type        = string
  default     = "application"
  description = "Load balancer type"

  validation {
    condition     = contains(["application", "network", "gateway"], var.load_balancer_type)
    error_message = "The load balancer type must be application, network or gateway."
  }
}

variable "load_balancer_internal" {
  type        = bool
  default     = false
  description = "Whether the load balancer is internal (true) or internet-facing (false)"
}

variable "load_balancer_deletion_protection" {
  type        = bool
  default     = false
  description = "Protects the load balancer from deletion (set to true for real production)"
}

variable "elb_security_group_name" {
  type        = string
  default     = "alb-secuity-group"
  description = "Name for the security group of the ELB instance"
}

variable "load_balancer_ingress_cidr_ipv4" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR for IPv4 for inbound traffic to the load balancer"
}

variable "load_balancer_egress_cidr_ipv4" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR for IPv4 for outbound traffic of the load balancer"
}

variable "load_balancer_egress_ip_protocol" {
  type        = string
  default     = "-1"
  description = "IP protocol for the outbound traffic of the load balancer (-1 means all)"
}

variable "load_balancer_listener_port" {
  type        = number
  default     = 80
  description = "Port on which the load balancer listens for HTTP, which it redirects to HTTPS"
}

variable "load_balancer_listener_protocol" {
  type        = string
  default     = "HTTP"
  description = "Protocol of the load balancer listener which redirects to HTTPS"
}

variable "load_balancer_https_listener_port" {
  type        = number
  default     = 443
  description = "Port on which the load balancer listens for HTTPS"
}

variable "load_balancer_ssl_policy" {
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  description = "TLS policy of the HTTPS listener"
}

variable "load_balancer_target_group_protocol" {
  type        = string
  default     = "HTTP"
  description = "Protocol between the load balancer and the EC2 instances, TLS ends at the load balancer"
}

variable "load_balancer_idle_timeout" {
  type        = number
  default     = 300
  description = "Seconds a connection may stay idle, an agent run streams for minutes and an upload is embedded before it returns"

  validation {
    condition     = var.load_balancer_idle_timeout >= 1 && var.load_balancer_idle_timeout <= 4000
    error_message = "The idle timeout must be between 1 and 4000 seconds."
  }
}

variable "load_balancer_target_group_name" {
  type        = string
  default     = "vela47-web-tg"
  description = "Name for the load balancer target group"
}

variable "load_balancer_health_check_path" {
  type        = string
  default     = "/"
  description = "Path which the load balancer checks for healthy EC2 instances"
}

# RDS database variables
variable "rds_instance_identifier" {
  type        = string
  default     = "vela47-db"
  description = "Identifier for the RDS instance"
}

variable "rds_engine" {
  type        = string
  default     = "postgres"
  description = "Database engine of the RDS instance, the server talks to PostgreSQL only"
}

variable "rds_engine_version" {
  type        = string
  default     = "17"
  description = "Major version of PostgreSQL, the same as the database container in development"
}

variable "rds_instance_class" {
  type        = string
  default     = "db.t4g.micro"
  description = "Instance class of the RDS instance"
}

variable "rds_allocated_storage" {
  type        = number
  default     = 20
  description = "Storage of the RDS instance in GB"
}

variable "rds_storage_type" {
  type        = string
  default     = "gp3"
  description = "Storage type of the RDS instance"
}

variable "rds_storage_encrypted" {
  type        = bool
  default     = true
  description = "Whether the storage of the RDS instance is encrypted"
}

variable "rds_database_name" {
  type        = string
  default     = "vela47"
  description = "Database created on the RDS instance, the same name the server uses by default"
}

variable "rds_master_username" {
  type        = string
  default     = "vela47"
  description = "Master user of the RDS instance, its password is created and rotated by RDS in Secrets Manager"
}

variable "rds_port" {
  type        = number
  default     = 5432
  description = "Port of the RDS instance, the server uses 5432 by default"
}

variable "rds_multi_az" {
  type        = bool
  default     = false
  description = "Whether a standby replica runs in another availability zone (set to true for real production, it doubles the price of the database)"
}

variable "rds_publicly_accessible" {
  type        = bool
  default     = false
  description = "Whether the RDS instance gets a public address"
}

variable "rds_backup_retention_period" {
  type        = number
  default     = 7
  description = "Days the automated backups of the RDS instance are kept"

  validation {
    condition     = var.rds_backup_retention_period >= 0 && var.rds_backup_retention_period <= 35
    error_message = "The backup retention period must be between 0 and 35 days."
  }
}

variable "rds_skip_final_snapshot" {
  type        = bool
  default     = true
  description = "Whether the RDS instance is deleted without a final snapshot (set to false for real production)"
}

variable "rds_deletion_protection" {
  type        = bool
  default     = false
  description = "Protects the RDS instance from deletion (set to true for real production)"
}

variable "rds_subnet_group_name" {
  type        = string
  default     = "vela47-db-subnet-group"
  description = "Name for the subnet group of the RDS instance"
}

variable "rds_security_group_name" {
  type        = string
  default     = "rds-database-sg"
  description = "Name for the security group of the RDS instance"
}

# Application secret variables
variable "app_secret_name" {
  type        = string
  default     = "vela47/app"
  description = "Name for the Secrets Manager secret holding the token signing key and the bootstrapped admin"
}

variable "app_secret_recovery_window_in_days" {
  type        = number
  default     = 0
  description = "Days a deleted secret can still be restored, 0 deletes it at once so the name is free for the next apply"

  validation {
    condition     = var.app_secret_recovery_window_in_days == 0 || (var.app_secret_recovery_window_in_days >= 7 && var.app_secret_recovery_window_in_days <= 30)
    error_message = "The recovery window must be 0 or between 7 and 30 days."
  }
}

variable "app_token_secret_length" {
  type        = number
  default     = 48
  description = "Length of the key which signs the session tokens"

  validation {
    condition     = var.app_token_secret_length >= 32
    error_message = "The server needs a token secret of at least 32 characters."
  }
}

variable "app_admin_username" {
  type        = string
  default     = "admin"
  description = "Username of the admin bootstrapped on the first start"
}

variable "app_admin_password_length" {
  type        = number
  default     = 24
  description = "Length of the password of the admin bootstrapped on the first start"

  validation {
    condition     = var.app_admin_password_length >= 12
    error_message = "The server needs an admin password of at least 12 characters."
  }
}

# Domain variables
variable "route53_zone_name" {
  type        = string
  default     = "y47.sevc.link"
  description = "Route 53 hosted zone which already exists in the account and holds the application domain"
}

variable "app_domain_name" {
  type        = string
  default     = "vela47.y47.sevc.link"
  description = "Domain the application is served on over HTTPS"
}

# Server variables
variable "app_container_name" {
  type        = string
  default     = "app"
  description = "Name for the server container in the task definition"
}

variable "app_container_port" {
  type        = number
  default     = 8000
  description = "Port on which the server in the container listens, the load balancer forwards to it"
}

variable "app_security_group_name" {
  type        = string
  default     = "vela47-app-task-sg"
  description = "Name for the security group of the server task, it takes traffic only from the load balancer"
}

variable "app_log_group_name" {
  type        = string
  default     = "/ecs/vela47-app"
  description = "CloudWatch log group of the server task"
}

variable "log_retention_days" {
  type        = number
  default     = 14
  description = "Days the logs of the server task and of the sandbox function are kept"
}

# ECS variables
variable "ecs_cluster_name" {
  type        = string
  default     = "vela47"
  description = "Name for the ECS cluster, user_data registers the EC2 instances in it"
}

variable "ecs_service_name" {
  type        = string
  default     = "vela47-app"
  description = "Name for the ECS service which keeps the server task running"
}

variable "ecs_task_family" {
  type        = string
  default     = "vela47-app"
  description = "Family of the server task definition"
}

variable "ecs_task_cpu" {
  type        = number
  default     = 1024
  description = "CPU units the server container reserves (1024 is one vCPU)"
}

variable "ecs_task_memory" {
  type        = number
  default     = 1536
  description = "Memory limit of the server container in MiB, the task is stopped beyond it"
}

variable "ecs_task_memory_reservation" {
  type        = number
  default     = 768
  description = "Memory in MiB reserved for the server container on the instance, two tasks have to fit during a deploy"
}

variable "ecs_desired_count" {
  type        = number
  default     = 1
  description = "Number of server tasks running"
}

variable "ecs_task_role_name" {
  type        = string
  default     = "vela47-app-task-role"
  description = "Name for the IAM role of the server task, it calls Bedrock and the sandbox function and reads the secrets"
}

variable "ecs_task_policy_name" {
  type        = string
  default     = "vela47-app-task-policy"
  description = "Name for the IAM role policy of the server task"
}

variable "ecs_task_execution_role_name" {
  type        = string
  default     = "vela47-app-task-execution-role"
  description = "Name for the IAM role ECS uses to pull the image and write the logs of the server task"
}

# ECR variables
variable "app_repository_name" {
  type        = string
  default     = "vela47-app"
  description = "Name for the ECR repository of the server image"
}

variable "sandbox_repository_name" {
  type        = string
  default     = "vela47-sandbox"
  description = "Name for the ECR repository of the sandbox function image"
}

variable "ecr_kept_images" {
  type        = number
  default     = 5
  description = "How many images each repository keeps, older ones are deleted"
}

variable "docker_context" {
  type        = string
  default     = "desktop-linux"
  description = "Docker context Terraform builds the images with, Docker Desktop on a Mac has no /var/run/docker.sock"
}

# Sandbox function variables
variable "sandbox_function_name" {
  type        = string
  default     = "vela47-sandbox"
  description = "Name for the Lambda function the TEST subagent runs its commands in, the same name the server calls"
}

variable "sandbox_memory_size" {
  type        = number
  default     = 512
  description = "Memory of the sandbox function in MB, the same limit a sandbox container has in development"
}

variable "sandbox_timeout" {
  type        = number
  default     = 90
  description = "Seconds the sandbox function may run, a command gets 60 and the rest is for copying the workspace in"
}

variable "sandbox_security_group_name" {
  type        = string
  default     = "vela47-sandbox-sg"
  description = "Name for the security group of the sandbox function, it allows no traffic in or out"
}

variable "sandbox_role_name" {
  type        = string
  default     = "vela47-sandbox-role"
  description = "Name for the IAM role of the sandbox function, it may only write its logs and attach to the VPC"
}

# Bedrock variables
variable "bedrock_model_ids" {
  type        = list(string)
  default     = ["eu.anthropic.claude-sonnet-5-5", "amazon.titan-embed-text-v2:0"]
  description = "Bedrock models the server task may call, the same IDs the server asks for in PROD, an eu. prefix is a cross-region inference profile that keeps the requests in EU regions"
}
