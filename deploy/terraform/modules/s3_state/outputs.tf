output "s3_bucket_id" {
  description = "Name of the state bucket, the bucket of every s3 backend of the environment"
  value       = aws_s3_bucket.this.id
}

output "s3_bucket_arn" {
  description = "ARN of the state bucket"
  value       = aws_s3_bucket.this.arn
}
