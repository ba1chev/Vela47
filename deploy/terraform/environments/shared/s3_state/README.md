# shared/s3_state

Creates the bucket that holds the Terraform state of every other root module except `local/docker`: `shared/<root>/` for the account-wide roots and `<environment>/<root>/` for dev, staging and prod. Apply it first, and only once, with your own credentials:

1. `terraform init && terraform apply` (the state is still local at this point)
2. Uncomment the `backend "s3"` block in `state.tf`
3. `terraform init -migrate-state` moves this root module's own state into the bucket
