# local/docker

The local environment on Docker Desktop: PostgreSQL and the server, each in its own container on its own network. Ollama runs on the host. The state stays local, since nothing here exists outside this machine.

```bash
terraform fmt && terraform init && terraform validate && terraform plan && terraform apply
terraform output -raw admin_password
```
