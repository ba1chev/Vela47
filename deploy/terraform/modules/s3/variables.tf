variable "bucket" {
  description = "Name of the bucket, unique across all of AWS"
  type        = string
}

variable "noncurrent_version_expiration_days" {
  description = "Days an overwritten or deleted version of an object is kept before it is deleted"
  type        = number
  default     = 90
}

variable "expiring_prefixes" {
  description = "Prefixes whose objects are deleted expiration_days after they are written, e.g. short-lived reports"
  type        = list(string)
  default     = []
}

variable "expiration_days" {
  description = "Days an object under one of expiring_prefixes is kept"
  type        = number
  default     = 30
}
