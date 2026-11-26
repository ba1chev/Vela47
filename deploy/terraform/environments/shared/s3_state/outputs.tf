output "s3_bucket_id" {
  description = "Name of the state bucket, the bucket of every s3 backend"
  value       = module.s3_state.s3_bucket_id
}
