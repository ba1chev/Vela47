# OpenID Connect between GitHub Actions and AWS

The workflows hold no AWS keys. Each job that needs AWS asks GitHub for a short-lived OpenID Connect token, and AWS STS exchanges it for temporary credentials of `vela47-role`. The role trusts only this repository, and only `main` and its GitHub environments.

## What was set up by hand

- The identity provider `token.actions.githubusercontent.com` in IAM, audience `sts.amazonaws.com`.
- The role `vela47-role`, with the trust policy below.

## Trust policy of `vela47-role`

The repository was created after GitHub switched new repositories to immutable subject claims (July 2026). Its `sub` therefore carries the owner and repository IDs: `repo:ba1chev@282053563/Vela47@1436127823:...` (`GET /repos/ba1chev/Vela47/actions/oidc/customization/sub` shows the prefix). A trust policy written in the old `repo:ba1chev/Vela47:...` form never matches.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:ba1chev@282053563/Vela47@1436127823:ref:refs/heads/main",
            "repo:ba1chev@282053563/Vela47@1436127823:environment:dev",
            "repo:ba1chev@282053563/Vela47@1436127823:environment:staging",
            "repo:ba1chev@282053563/Vela47@1436127823:environment:prod"
          ]
        }
      }
    }
  ]
}
```

| Job | Its `sub` |
|---|---|
| delivery images and publish, deployment preview | `...:ref:refs/heads/main` |
| deployment deploy | `...:environment:<environment>` |

Pull requests, branches other than `main` and forks match none of them, so CI never reaches AWS. The environment form is extrapolated from the documented prefix. If the first deploy job is refused, read the `sub` from the error in CloudTrail and correct the policy.

## Permissions

The permissions are not edited by hand. `deploy/terraform/environments/shared/iam` attaches the policy `vela47-ci` to the role and creates the boundary `vela47-boundary`. Apply it with your own credentials:

```bash
cd deploy/terraform/environments/shared/iam
terraform init && terraform apply
```

| Area | Allowed |
|---|---|
| Terraform state | read and write under `dev/`, `staging/`, `prod/` of `vela47-terraform-state`, never `shared/` |
| Artifacts | read and write in `vela47-artifacts`, never delete |
| ECR | log in, push and pull `vela47-*` |
| Environment services | ACM, Auto Scaling, CloudWatch, EC2, ECS, ELB, Lambda, CloudWatch Logs, RDS, EventBridge Scheduler, only in `eu-central-1` |
| EC2 instance types | only t4g.nano, t4g.small, t4g.medium |
| Secrets Manager | only `vela47-*` secrets |
| Route 53 | records in the existing zone |
| IAM | only roles and instance profiles named `vela47-*`, created only with `vela47-boundary` attached, passed only to EC2, ECS, ECS tasks, Lambda and the scheduler |
| Denied | any change to `vela47-role`, `vela47-ci` or `vela47-boundary`, removing a boundary |

The boundary caps every role the pipeline creates at what the environments need: Bedrock, secrets, the sandbox function, ECS, ECR pulls, logs, Session Manager and the night schedule. It denies IAM, STS and Organizations. Even a role the pipeline writes by mistake can never grant more than that, and the pipeline can never widen its own permissions. That only happens through a pull request to `shared/iam` and an apply by hand.

The first deployments may still meet an `AccessDenied` for an action the list missed. The error names the action. Add it in `modules/ci_role` and apply `shared/iam` again.

## GitHub settings

- Repository variable `AWS_ROLE_ARN`: `arn:aws:iam::<account-id>:role/vela47-role`.
- Environments `dev`, `staging`, `prod`, deployment branches limited to `main`. `staging` and `prod` have required reviewers.
- Repository secret `TAVILY_API_KEY` (Settings → Secrets and variables → Actions → Secrets). Both jobs of a deployment read it: the preview has no environment, so it cannot see an environment secret. Without it, the server falls back to DuckDuckGo.
- Branch protection on `main`: pull requests only, the CI jobs required.
