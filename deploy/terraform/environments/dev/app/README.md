# dev/app

The server of dev: ECS on EC2 behind an ALB at `https://vela47-dev.y47.sevc.link`, the sandbox Lambda function, their roles and the application secret. It builds nothing: `release_version` names a release in the artifacts bucket, and its `release.yaml` gives the image digests. Deployments are ROLLING, and the `schedule` module stops the environment outside office hours.

```bash
terraform init
terraform plan -var release_version=<version>
```

The deployment workflow applies it after `dev/vpc/eu-central-1` and `dev/database`.
