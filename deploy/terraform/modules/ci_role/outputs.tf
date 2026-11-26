output "iam_policy_boundary_arn" {
  description = "ARN of the permissions boundary every role of the AWS environments carries"
  value       = aws_iam_policy.boundary.arn
}

output "iam_policy_ci_arn" {
  description = "ARN of the policy of the CI role"
  value       = aws_iam_policy.ci.arn
}
