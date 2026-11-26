output "ecr_repository_urls" {
  description = "URL of every repository, by repository"
  value       = module.ecr.ecr_repository_urls
}
