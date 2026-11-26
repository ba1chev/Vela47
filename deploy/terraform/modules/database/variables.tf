variable "name" {
  description = "Identifier of the RDS instance, also the name of its subnet group and security group"
  type        = string
}

variable "vpc_id" {
  description = "VPC the security group of the instance is created in"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnets of the subnet group, in at least 2 availability zones"
  type        = list(string)
}

variable "engine_version" {
  description = "Major version of PostgreSQL, the same as the database container in development"
  type        = string
  default     = "17"
}

variable "instance_class" {
  description = "Instance class of the RDS instance"
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  description = "Storage of the RDS instance in GB"
  type        = number
  default     = 20
}

variable "storage_type" {
  description = "Storage type of the RDS instance"
  type        = string
  default     = "gp3"
}

variable "db_name" {
  description = "Database created on the RDS instance, the same name the server uses by default"
  type        = string
  default     = "vela47"
}

variable "username" {
  description = "Master user of the RDS instance, its password is created and rotated by RDS in Secrets Manager"
  type        = string
  default     = "vela47"
}

variable "port" {
  description = "Port of the RDS instance, the server uses 5432 by default"
  type        = number
  default     = 5432
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

  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35
    error_message = "The backup retention period must be between 0 and 35 days."
  }
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

variable "backup_window" {
  description = "Daily UTC window of the automated backup, before the maintenance window"
  type        = string
  default     = "01:00-02:00"
}

variable "maintenance_window" {
  description = "Weekly UTC window in which RDS applies minor version upgrades and patches"
  type        = string
  default     = "sun:02:30-sun:03:30"
}
