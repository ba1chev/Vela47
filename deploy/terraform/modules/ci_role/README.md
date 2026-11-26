# ci_role

The permissions of the role GitHub Actions assumes through OpenID Connect. The identity provider and the role itself were created by hand; their trust policy is in `docs/open_id_connect.md`. This module attaches the policy of what the workflows do, and creates the permissions boundary every role of an AWS environment carries.

- State: read and write only under the prefixes of the AWS environments, never `shared/`.
- Artifacts: read and write releases and deployment records, never delete.
- ECR: push and pull the repositories of the project.
- The services an environment is made of, in one region only. EC2 may launch only the instance types the environments use.
- IAM: only roles and instance profiles named after the project, created only with the boundary, passed only to the services that run them. The CI role, its policy and the boundary can never be changed by the pipeline itself, so widening its permissions always goes through a pull request and a local apply of `shared/iam`.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
