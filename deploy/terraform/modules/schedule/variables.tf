variable "name" {
  description = "Prefix of the names of the schedules and their role, vela47-<environment>"
  type        = string
}

variable "permissions_boundary_arn" {
  description = "Permissions boundary of the role of the scheduler"
  type        = string
}

variable "cluster_name" {
  description = "ECS cluster of the service"
  type        = string
}

variable "service_name" {
  description = "ECS service whose task count is set to 0 in the evening and back in the morning"
  type        = string
}

variable "service_arn" {
  description = "ARN of that service"
  type        = string
}

variable "desired_count" {
  description = "Task count the service gets back in the morning"
  type        = number
}

variable "db_instance_identifier" {
  description = "RDS instance stopped in the evening and started in the morning"
  type        = string
}

variable "db_instance_arn" {
  description = "ARN of that RDS instance"
  type        = string
}

variable "timezone" {
  description = "Time zone of the schedule expressions"
  type        = string
  default     = "Europe/Sofia"
}

variable "stop_expression" {
  description = "When the server tasks stop, after the end of the working day"
  type        = string
  default     = "cron(0 20 ? * MON-FRI *)"
}

variable "stop_database_expression" {
  description = "When the database stops, after the server tasks are gone"
  type        = string
  default     = "cron(10 20 ? * MON-FRI *)"
}

variable "start_database_expression" {
  description = "When the database starts, early enough to be available before the server tasks"
  type        = string
  default     = "cron(30 7 ? * MON-FRI *)"
}

variable "start_expression" {
  description = "When the server tasks start"
  type        = string
  default     = "cron(0 8 ? * MON-FRI *)"
}
