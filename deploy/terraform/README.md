# Terraform

The infrastructure of Vela47, laid out after [terraform-kickstart](https://github.com/SeveralClouds/terraform-kickstart). Every directory under `environments/` is a root module with its own state. The resources themselves live in `modules/`.

    deploy
    ├── images                          # Dockerfiles and the sandbox handler, built by the modules below
    │   ├── dev                         # app, database, sandbox (compose project)
    │   └── prod                        # app, sandbox (Lambda)
    └── terraform
        ├── environments
        │   ├── dev
        │   │   └── docker              # local Docker: PostgreSQL + server, local state
        │   └── prod
        │       ├── global
        │       │   └── s3_state        # first thing to apply: the bucket for every other state
        │       ├── vpc
        │       │   └── eu-central-1    # VPC, subnets, internet and NAT gateways
        │       ├── database            # RDS PostgreSQL
        │       └── app                 # ECR, ECS on EC2, ALB, DNS, sandbox Lambda, IAM, secrets
        └── modules
            ├── s3_state
            ├── vpc
            ├── database
            ├── app
            ├── docker_database
            └── docker_app

## Production order

The root modules read each other's outputs through `terraform_remote_state`. That means they are applied in this order and destroyed in the reverse order:

1. `prod/global/s3_state`: once, then migrate its own state into the bucket (see its README)
2. `prod/vpc/eu-central-1`
3. `prod/database`
4. `prod/app`

In every root module run:

```bash
terraform fmt && terraform init && terraform validate && terraform plan && terraform apply
```

## Conventions

These follow the internal Terraform best practices:

- Every resource gets `owner`, `project`, `environment` and `created_by` through `default_tags` of the provider.
- Names use underscores and never repeat the resource type. A module's only resource of a type is named `this`.
- Variable keys go in the order `description`, `type`, `default`, `validation`.
- Outputs are named `{name}_{type}_{attribute}`.
- Root modules configure providers and backends, and modules only declare `required_providers`.
- `pre-commit` (see `.pre-commit-config.yaml` at the repository root) runs `fmt`, `validate` and `terraform-docs`.
- A shared plugin cache avoids downloading the providers once per root module: `export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"`.
