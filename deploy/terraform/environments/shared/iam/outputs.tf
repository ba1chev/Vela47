output "iam_policy_boundary_arn" {
  description = "ARN of the permissions boundary every role of the AWS environments carries"
  value       = module.ci_role.iam_policy_boundary_arn
}

output "iam_policy_ci_arn" {
  description = "ARN of the policy attached to the CI role"
  value       = module.ci_role.iam_policy_ci_arn
}
