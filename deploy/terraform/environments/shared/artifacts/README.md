# shared/artifacts

The bucket of continuous delivery. The delivery workflow writes every release to `releases/<version>/`: its `release.yaml` (version, commit, change classes and the image digests) and `deploy.tar.gz` (the Terraform and the pipeline scripts of that commit). Release objects are never overwritten. The deployment workflow reads a release from here and records what each environment runs in `deployments/<environment>/current.yaml`, with every deployment also kept under `deployments/<environment>/history/`.

Applied once by hand after `shared/s3_state`.
