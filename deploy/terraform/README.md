# Terraform

The infrastructure of Vela47, laid out after [terraform-kickstart](https://github.com/SeveralClouds/terraform-kickstart). Every directory under `environments/` is a root module with its own state. The resources themselves live in `modules/`.

    deploy
    ├── images                          # Dockerfiles and the sandbox handler
    │   ├── local                       # app, database, sandbox (compose project), built by local/docker
    │   └── aws                         # app, sandbox (Lambda), built once per release by the delivery workflow
    ├── pipeline                        # release rules, plan guard, rollout and smoke test the workflows run
    ├── release.yaml                    # the release the current commit becomes (docs/release_process.md)
    └── terraform
        ├── environments
        │   ├── local
        │   │   └── docker              # Docker Desktop: PostgreSQL + server, local state, Ollama on the host
        │   ├── shared                  # once per account, applied by hand
        │   │   ├── s3_state            # the bucket of every other state
        │   │   ├── iam                 # permissions of the CI role and the boundary of every role
        │   │   ├── artifacts           # releases and deployment records
        │   │   └── ecr                 # vela47-app, vela47-sandbox
        │   ├── dev                     # deployed on every merge into main
        │   ├── staging                 # deployed after an approval
        │   └── prod                    # deployed after an approval, identical to staging
        │       ├── vpc/eu-central-1    # VPC, subnets, internet gateway, NAT
        │       ├── database            # RDS PostgreSQL
        │       └── app                 # ECS on EC2, ALB, DNS, sandbox Lambda, IAM, secrets, alarms
        └── modules
            ├── s3_state, s3, ecr, ci_role
            ├── vpc, database, app, schedule
            └── docker_database, docker_app

## Environments

| | local | dev | staging | prod |
|---|---|---|---|---|
| Runs on | Docker Desktop | AWS | AWS | AWS |
| Models | Ollama on the host | Bedrock | Bedrock | Bedrock |
| Applied by | you | the pipeline, on every release | the pipeline, after an approval | the pipeline, after an approval |
| State | local | `dev/<root>/` in S3 | `staging/<root>/` in S3 | `prod/<root>/` in S3 |

dev is as cheap as the architecture allows: one t4g.small that ECS scales to 0 outside office hours, a NAT instance instead of a NAT gateway, a Single-AZ database stopped at night, rolling deployments. staging and prod are the same modules with the same values: two t4g.medium in two zones, a NAT gateway, a Multi-AZ database with 14 days of backups and deletion protection, canary deployments. A unit test keeps staging and prod identical apart from their name, domain and address range. `docs/change_management.md` has the full comparison.

## Order

The root modules read each other's outputs through `terraform_remote_state`, so they are applied in this order and destroyed in reverse (`docs/deployment_order.md`):

1. `shared/s3_state`, `shared/iam`, `shared/artifacts`, `shared/ecr`: once, by hand, with `deploy/bootstrap.sh`
2. `<environment>/vpc/eu-central-1`
3. `<environment>/database`
4. `<environment>/app`, with `-var release_version=<version>` naming a release in the artifacts bucket

Steps 2 to 4 are what the deployment workflow does. Running them by hand works the same way:

```bash
cd deploy/terraform/environments/dev/app
terraform init && terraform plan -var release_version=1.0.0
```

## Conventions

These follow the internal Terraform best practices:

- Every resource gets `owner`, `project`, `environment` and `created_by` through `default_tags` of the provider.
- Names use underscores and never repeat the resource type. A module's only resource of a type is named `this`.
- Variable keys go in the order `description`, `type`, `default`, `validation`.
- Outputs are named `{name}_{type}_{attribute}`.
- Root modules configure providers and backends, and modules only declare `required_providers`.
- Every IAM role carries the permissions boundary `vela47-boundary`.
- A checkov finding is fixed or skipped next to the resource with `#checkov:skip=<id>:<reason>`.
- `pre-commit` (see `.pre-commit-config.yaml` at the repository root) runs `fmt`, `validate`, `tflint`, `terraform-docs` and checkov. CI runs all of them except `terraform-docs`.
- A shared plugin cache avoids downloading the providers once per root module: `export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"`.
