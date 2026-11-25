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
  description = "Identifier of the RDS instance, also the name of its subnet group and security group"
  type        = string
  default     = "vela47"
}

variable "instance_class" {
  description = "Instance class of the RDS instance"
  type        = string
  default     = "db.t4g.micro"
}

variable "multi_az" {
  description = "Whether a standby replica runs in another availability zone (true for real production, it doubles the price of the database)"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Days the automated backups of the RDS instance are kept"
  type        = number
  default     = 7
}

variable "skip_final_snapshot" {
  description = "Whether the RDS instance is deleted without a final snapshot (false for real production)"
  type        = bool
  default     = true
}

variable "deletion_protection" {
  description = "Protects the RDS instance from deletion (true for real production)"
  type        = bool
  default     = false
}
