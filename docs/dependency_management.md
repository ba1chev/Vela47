# Dependency management

Every dependency is pinned to an exact version or digest, so a build is repeatable and an update is a visible, reviewed change. Dependabot proposes the updates (`.github/dependabot.yml`), weekly and grouped per ecosystem.

## What is pinned where

| Dependency | Pinned in | How |
|---|---|---|
| Python packages of the server | `requirements.txt` | exact versions |
| Test and tooling packages | `requirements-dev.txt` | exact versions, on top of `requirements.txt` |
| Packages of the pipeline scripts | `deploy/pipeline/requirements.txt` | exact versions |
| Base images | `deploy/images/**/Dockerfile` | tag and `@sha256` digest |
| Terraform | workflows (`terraform_version`), `required_version` in every root | exact in CI, minimum in code |
| Terraform providers | `versions.tf` and `.terraform.lock.hcl` of every root | `~> 6.0` for AWS, exact for the others; the lock file pins the build with hashes for linux and macOS |
| GitHub Actions | workflows | full commit SHA, version in a comment |
| tflint and its AWS ruleset | `ci.yaml`, `.tflint.hcl` | exact versions |
| pre-commit hooks | `.pre-commit-config.yaml` | exact tag |

The production image installs `requirements.txt` only. Test tools stay out of it.

## Updating

1. Dependabot opens a pull request, or you change a pin by hand on a `fix/` or `infra/` branch.
2. An update of what runs on AWS (Python packages, images, providers) is a release. Raise the patch version in `deploy/release.yaml` on the same branch. A provider update counts as `infrastructure: additive` only if the plan changes something.
3. CI checks it like any other change, and the release is promoted through dev and staging before prod.

After changing a provider version, refresh the lock files for every platform CI and developers use:

```bash
terraform providers lock -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_arm64
```

## Dependencies between parts of the system

**Between root modules.** `app` reads the outputs of `vpc` and `database` through `terraform_remote_state`. Those outputs are the contract between them: renaming or removing one is a `breaking` change, adding one is `additive`. The order this imposes is in `deployment_order.md`.

**Between modules and roots.** Modules live in this repository and are referenced by path. They are not versioned on their own: the release is the version. `deploy.tar.gz` of a release holds the modules and the roots of that commit, so an environment always runs one consistent set of both, and promoting a release promotes its infrastructure with its code.

**Between the application and the infrastructure.** A release declares in `deploy/release.yaml` what it needs from the infrastructure and the schema. The rules in `change_management.md` make sure the infrastructure a release needs exists before its code runs, and is removed only after no running release needs it.

**Between the code and the Terraform.** Unit tests keep them in step: the models the server calls are the ones IAM allows, the sandbox function the server calls is the one Terraform creates, and staging stays identical to prod.

**Shared resources.** The ECR repositories, the artifacts bucket and the state bucket are shared by all environments and managed in `shared/`, outside the release cycle.
