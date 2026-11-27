# local/docker

The local environment on Docker Desktop: PostgreSQL and the server, each in its own container on its own network. The models run on Ollama on the host, or on Bedrock with `model_client = "bedrock"`, called with the host's `~/.aws` credentials, as in the AWS environments. The state stays local, since nothing here exists outside this machine.

```bash
terraform fmt && terraform init && terraform validate && terraform plan && terraform apply
terraform apply -var model_client=bedrock
terraform output -raw admin_password
```
