# staging/app

The server of staging: ECS on EC2 behind an ALB at `https://vela47-staging.y47.sevc.link`, the sandbox Lambda function, their roles and the application secret. It builds nothing: `release_version` names a release in the artifacts bucket, and its `release.yaml` gives the image digests. Deployments are CANARY: 10% of the traffic, then all of it, the old tasks kept for ten minutes.

```bash
terraform init
terraform plan -var release_version=<version>
```

The deployment workflow applies it after `staging/vpc/eu-central-1` and `staging/database`.
