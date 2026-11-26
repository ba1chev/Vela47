module "ecr" {
  source = "../../../modules/ecr"

  name                = var.name
  repositories        = ["app", "sandbox"]
  lambda_repositories = ["sandbox"]
  kept_images         = var.kept_images
}
