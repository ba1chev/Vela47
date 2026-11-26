variable "name" {
  description = "Prefix of the repository names, a repository is named <name>-<repository>"
  type        = string
}

variable "repositories" {
  description = "Repositories to create, one per image of a release"
  type        = list(string)
}

variable "lambda_repositories" {
  description = "Repositories whose images Lambda functions of the project run, Lambda gets pull access to them"
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for current in var.lambda_repositories : contains(var.repositories, current)])
    error_message = "Every repository in lambda_repositories must also be in repositories."
  }
}

variable "kept_images" {
  description = "How many tagged images each repository keeps, older ones are deleted"
  type        = number
  default     = 30
}
