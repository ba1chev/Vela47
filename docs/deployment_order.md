# Deployment order

The Terraform of the AWS environments is split into root modules, each with its own state in `vela47-terraform-state`. A root reads the outputs of the roots it builds on through `terraform_remote_state`. That fixes the order in which they are applied, and the reverse order in which they are destroyed.

## Once per account (by hand)

`deploy/bootstrap.sh` does all of it, run once with administrator credentials in the AWS CLI, never by the pipeline. It asks before every apply (`--yes` skips the questions) and is safe to run again:

1. The GitHub OpenID Connect provider, if the account has none, and the role `vela47-role` with the trust policy of this repository and two-hour sessions (`open_id_connect.md`).
2. `shared/s3_state`: the state bucket. Its own state starts local and is moved into the bucket right after.
3. `shared/iam`: the permissions of `vela47-role` and the permissions boundary.
4. `shared/artifacts` and `shared/ecr`: the artifacts bucket and the image repositories.

It ends with what only GitHub can hold: the variable `AWS_ROLE_ARN`, the secret `TAVILY_API_KEY`, the environments and the branch protection. Only then can the first release be delivered.

## Every deployment of a release into one environment

| Step | Why here |
|---|---|
| 1. Start the database if the night schedule stopped it (dev) | Terraform cannot change a stopped instance, and the server needs it |
| 2. `vpc/eu-central-1` | everything else lives in its subnets |
| 3. `database` | reads the subnets; the server reads its address and secret |
| 4. Snapshot the database (staging, prod) | the new release migrates the schema when it starts |
| 5. `app` | reads both; registers the new task definition and starts the ECS deployment |
| 6. Follow the rollout, smoke test | a failure rolls back before the old tasks are gone |
| 7. Record the outcome | `current.yaml` moves only on success |

Infrastructure always goes before the code that uses it, and the schema is migrated before the new code takes traffic. This is what makes `additive` and `expand` changes safe to ship together with code (`change_management.md`). Every step plans first and refuses a plan the release did not declare.

A root with no changes is planned and skipped. The preview plans all three roots before the approval. When an earlier root has changes, a later root may only be planned after it is applied, and the preview says so.

## Environments

A release goes dev → staging → prod, the same artifact each time. Each deployment is checked against the records: staging only takes a release that succeeded in dev, prod only one that succeeded in staging.

## Destroying an environment

The Teardown workflow does it (`release_process.md`), in the reverse order: `app`, then `database`, then `vpc/eu-central-1`.

- `app` goes first because the ECS agent confirms stopped tasks through the NAT, and the instances need their role until they are gone. That is why the auto scaling group depends on the role's policy attachments.
- The server tasks are stopped first, so the service does not wait for them to drain.
- In staging and prod the deletion protection of the database and the load balancer is lifted first, with a targeted apply. `PlanGuard` still refuses to delete a database in a deployment; only the Teardown workflow does.
- Lambda keeps the network interfaces of the sandbox function for up to half an hour after the function is gone, and its security group cannot be deleted before them. The workflow deletes them as soon as AWS releases them.

The `shared` roots stay. The state bucket is protected by `prevent_destroy`.
