# prod/global/s3_state

Creates the bucket that holds the Terraform state of every other production root module. Apply it first, and only once:

1. `terraform init && terraform apply` (the state is still local at this point)
2. Uncomment the `backend "s3"` block in `state.tf`
3. `terraform init -migrate-state` moves this root module's own state into the bucket
