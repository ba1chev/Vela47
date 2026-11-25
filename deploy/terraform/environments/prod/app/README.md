# prod/app

The Vela47 server in production: ECS on one Graviton EC2 instance behind an HTTPS ALB, the sandbox Lambda function, the ECR images and the application secret. It reads the `vpc` and `database` root modules through `terraform_remote_state`.

Docker Desktop has to be running during `apply`, because Terraform builds both images on this machine and pushes them to ECR. Set the optional search key with `TF_VAR_tavily_api_key`.

Order: apply last, destroy first. If `vpc` were destroyed first, the ECS agent would lose its route through the NAT gateway and a destroy would hang on a task stuck in STOPPING.
