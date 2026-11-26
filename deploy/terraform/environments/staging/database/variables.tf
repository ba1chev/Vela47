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
  description = "Identifier of the RDS instance, also the name of its subnet group and security group"
  type        = string
  default     = "vela47-staging"
}

variable "state_bucket" {
  description = "Bucket of the Terraform state, created by shared/s3_state"
  type        = string
  default     = "vela47-terraform-state"
}

variable "instance_class" {
  description = "Instance class of the RDS instance"
  type        = string
  default     = "db.t4g.micro"
}

variable "multi_az" {
  description = "Whether a standby replica runs in another availability zone, it doubles the price of the database"
  type        = bool
  default     = true
}

variable "backup_retention_period" {
  description = "Days the automated backups are kept, the database can be restored to any second in them"
  type        = number
  default     = 14
}

variable "skip_final_snapshot" {
  description = "Whether the RDS instance is deleted without a final snapshot"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Protects the RDS instance from deletion"
  type        = bool
  default     = true
}
