# ecr

The ECR repositories of a release, shared by every AWS environment. The delivery workflow builds each image once, tags it with the release version and pushes it here; every environment then runs it by digest. Tags are immutable, images are scanned on push, untagged images expire after a day, and the newest `kept_images` stay, so an older release can still be redeployed.

Lambda gets pull access to the repositories in `lambda_repositories`, limited to functions named `<name>-*` in this account and region.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
