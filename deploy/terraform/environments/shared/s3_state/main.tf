module "s3_state" {
  source = "../../../modules/s3_state"

  bucket = var.state_bucket
}
