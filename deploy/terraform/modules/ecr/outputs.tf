output "ecr_repository_urls" {
  description = "URL of every repository, by repository"
  value       = { for current_name, current in aws_ecr_repository.this : current_name => current.repository_url }
}
