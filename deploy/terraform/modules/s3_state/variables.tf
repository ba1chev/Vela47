variable "bucket" {
  description = "Name of the bucket which holds the Terraform state, unique across all of AWS"
  type        = string
}

variable "noncurrent_version_expiration_days" {
  description = "Days an overwritten or deleted version of a state is kept before it is deleted"
  type        = number
  default     = 90
}
