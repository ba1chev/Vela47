# Paths of the images, and the files whose change rebuilds the server image
locals {
  repository       = abspath("${path.module}/../..")
  app_dockerfile   = "deploy/dev/images/app_image/Dockerfile"
  database_context = "${local.repository}/deploy/dev/images/db_image"
  source_files = sort([
    for current_file in setunion(
      fileset(local.repository, "app/**"),
      fileset(local.repository, "db/**"),
      fileset(local.repository, "deploy/dev/images/sandbox_image/**"),
      ["requirements.txt", local.app_dockerfile]
    ) : current_file if !strcontains(current_file, "__pycache__") && !strcontains(current_file, ".sqlite3")
  ])
}
