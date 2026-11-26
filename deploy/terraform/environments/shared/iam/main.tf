module "ci_role" {
  source = "../../../modules/ci_role"

  name             = var.name
  role_name        = var.ci_role_name
  region           = var.region
  environments     = var.environments
  state_bucket     = var.state_bucket
  artifacts_bucket = var.artifacts_bucket
  instance_types   = var.instance_types
}
