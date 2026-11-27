# Release process

How a change travels from a branch to production. Three stages, kept apart on purpose:

| Stage | Workflow | Trigger | Result |
|---|---|---|---|
| Continuous integration | `.github/workflows/ci.yaml` | every pull request into `main` | the change is checked, nothing is built for AWS |
| Continuous delivery | `.github/workflows/delivery.yaml` | every merge into `main` that declares a new version | a release: images in ECR, `releases/<version>/` in S3, git tag `v<version>` |
| Continuous deployment | `.github/workflows/deployment.yaml` | the delivery workflow, or by hand | the release runs in one environment |

A release is built once and promoted unchanged: dev at once, staging after an approval, prod after another one.

## Branches

`main` is the only long-lived branch. It is protected: changes arrive through pull requests only, and every CI job must pass before a merge. There are no release branches. A release is a tag on `main`.

| Branch | For |
|---|---|
| `feature/<name>` | new behaviour of the application |
| `fix/<name>` | a bug fix |
| `infra/<name>` | Terraform, images, workflows, the pipeline |
| `hotfix/<name>` | an urgent fix of what runs in prod, merged and promoted at once |
| `docs/<name>` | documentation only, never a release |
| `dependabot/...` | dependency updates opened by Dependabot |

`<name>` is lower case, words joined by `-`. CI rejects any other branch name.

Commit messages stay as they are in this repository: `Add|Update|Remove <path or thing>`, one file per commit.

## Versions

Every release has a semantic version, declared in `deploy/release.yaml` together with the kind of change it carries (see `change_management.md`):

```yaml
version: 1.4.0
infrastructure: additive   # none | additive | breaking
database: expand           # none | expand | contract
summary: One line on what the release changes
```

- MAJOR: a breaking infrastructure change or a contract migration. These always ship alone.
- MINOR: new behaviour, new resources or capacity, an expand migration.
- PATCH: a fix or a dependency update.

A pull request that changes what runs on AWS (`app/`, `db/`, `requirements.txt`, `deploy/images/aws/`, `deploy/pipeline/`, `deploy/terraform/modules/`, `deploy/terraform/environments/{dev,staging,prod}/`) must raise the version above the newest tag. Documentation, tests, the local environment and the shared roots with their modules (`s3_state`, `s3`, `ecr`, `ci_role`, applied by `deploy/bootstrap.sh`) need no release. CI checks all of this (`ReleaseRules`).

## Continuous integration

`ci.yaml` runs on every pull request, in parallel, without AWS credentials:

1. Branch name.
2. Release rules: `deploy/release.yaml` against the changed paths.
3. Unit tests (`pytest`), including the tests that keep the code and the Terraform in step and staging identical to prod.
4. Terraform: `fmt -check`, `init -backend=false` and `validate` of every root module, `tflint`.
5. Checkov over Terraform, Dockerfiles and workflows. A finding is either fixed or skipped next to the resource with its reason.
6. Both AWS images are built for arm64, without pushing.

## Continuous delivery

`delivery.yaml` runs on every push to `main`. If `v<version>` already exists, the merge changed nothing that runs and the workflow stops. Otherwise:

1. Both images are built once on an arm64 runner and pushed to `vela47-app` and `vela47-sandbox` with the tag `<version>`. Tags are immutable.
2. `releases/<version>/` is written to `vela47-artifacts`:
   - `release.yaml`: the manifest, the commit and the digest of each image. The app root of every environment reads its images from here.
   - `deploy.tar.gz`: `deploy/` of that commit (Terraform, pipeline scripts). A deployment runs this copy, never the branch.

   Neither object is ever overwritten (`--if-none-match`).
3. A GitHub release `v<version>` is created on the commit.

A failed run can be re-run: images and objects already stored are reused.

## Continuous deployment

`deployment.yaml` deploys one stored release into one environment:

1. **Preview** (no approval): checks the promotion, plans `vpc`, `database` and `app`, and refuses any plan the release did not declare (`PlanGuard`). The plan summary is the job summary.
2. **Deploy** (GitHub environment `dev`, `staging` or `prod`): starts a database stopped for the night, applies `vpc` and `database`, snapshots the database (staging, prod), applies `app`, follows the ECS deployment, smoke tests it, and records the outcome.

| | dev | staging | prod |
|---|---|---|---|
| Starts | after delivery | after dev, with approval | after staging, with approval |
| ECS strategy | ROLLING | CANARY (10%, 5 min, 100%, 10 min bake) | CANARY |
| Smoke test | after the deployment | during the bake time | during the bake time |
| On failure | the pipeline fails | ECS rolls back at once | ECS rolls back at once |
| Snapshot before migrating | no | yes | yes |

ROLLING is used where a short outage costs nothing and no spare capacity is wanted. CANARY starts a full set of new tasks in the idle target group, sends 10% of the traffic to them while the alarms (5xx, unhealthy tasks) watch, then all of it, and keeps the old tasks for ten minutes so a rollback is a weight change. Linear shifting adds nothing at two tasks and little traffic, so it is not used.

A release goes to staging only after it succeeded in dev, and to prod only after staging. The deployment checks this against the records, so a hand-started deployment cannot skip a stage. It also refuses to deploy to staging or prod while their GitHub environment has no required reviewers, so a missing setting never turns into an unapproved deployment.

## Records

Each environment has `deployments/<environment>/current.yaml` in `vela47-artifacts`, with the version it runs, the version before it, the commit, the time, the run and the actor. Every attempt, failed or not, is kept under `deployments/<environment>/history/`. GitHub also lists the deployments of each environment on the repository page.

## Rollback

- During a canary deployment ECS rolls back by itself when an alarm goes off or the smoke test fails.
- After a deployment finished, redeploy the previous release: `gh workflow run deployment.yaml -f environment=prod -f version=<previous>`, with `previous` read from `current.yaml`. Releases are only additive within one major version (see `change_management.md`), so the previous code runs on the newer schema.
- A database is never rolled back by the pipeline. See `change_management.md`.

## Teardown

`.github/workflows/teardown.yaml` removes one AWS environment completely, for when it is not needed and should cost nothing: **Actions → Teardown → Run workflow**, pick the environment and type its name again. Only the owner of the repository can start it, only from `main`, and staging and prod also wait for the approval of their GitHub environment. It never runs at the same time as a deployment of the same environment.

It runs the Terraform of the release the environment runs, stops the server tasks, lifts the deletion protection of the database and the load balancer and the recovery window of the application secret, then destroys the server, the database and the network (`deployment_order.md`). In staging and prod the database leaves a final snapshot, `vela47-<environment>-final`; only the newest one is kept. `deployments/<environment>/current.yaml` then names no release and remembers the last one. The next deployment builds the environment from scratch.

## Hotfix

Branch `hotfix/<name>` from `main`, raise the patch version, merge. The release goes through dev, staging and prod like any other, with both approvals given at once.
