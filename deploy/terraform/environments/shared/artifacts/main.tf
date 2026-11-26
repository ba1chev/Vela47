module "s3" {
  source = "../../../modules/s3"

  bucket                             = var.artifacts_bucket
  noncurrent_version_expiration_days = var.noncurrent_version_expiration_days
}
