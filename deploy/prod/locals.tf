# Tags shared by all tagged resources
locals {
  common_tags = {
    Name        = var.resource_name_tag
    Environment = var.environment_tag
  }
}

# Bedrock models the server task may call
# An ID with a geography prefix (eu.) is an inference profile, which routes a request to one of several regions,
# so the task needs the profile itself and the base model in every region it can be routed to
data "aws_caller_identity" "current" {}

locals {
  bedrock_base_model_ids = [for current in var.bedrock_model_ids : replace(current, "/^(eu|us|apac|global)\\./", "")]
  bedrock_resources = concat(
    [for current in local.bedrock_base_model_ids : "arn:aws:bedrock:*::foundation-model/${current}"],
    [
      for current in var.bedrock_model_ids : "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/${current}"
      if !contains(local.bedrock_base_model_ids, current)
    ]
  )
}

# Paths of the images, and the files whose change rebuilds each of them
# An image is tagged with a hash of its files, so a change gives a new tag and ECS deploys it
locals {
  repository      = abspath("${path.module}/../..")
  app_dockerfile  = "deploy/prod/images/app_image/Dockerfile"
  sandbox_context = "${local.repository}/deploy/prod/images/sandbox_lambda"
  app_source_files = sort([
    for current_file in setunion(
      fileset(local.repository, "app/**"),
      fileset(local.repository, "db/**"),
      ["requirements.txt", local.app_dockerfile]
    ) : current_file if !strcontains(current_file, "__pycache__") && !strcontains(current_file, ".sqlite3")
  ])
  app_image_tag = substr(sha1(join("", [
    for current_file in local.app_source_files : filesha1("${local.repository}/${current_file}")
  ])), 0, 12)
  sandbox_image_tag = substr(sha1(join("", [
    for current_file in sort(fileset(local.sandbox_context, "*")) : filesha1("${local.sandbox_context}/${current_file}")
  ])), 0, 12)
}
