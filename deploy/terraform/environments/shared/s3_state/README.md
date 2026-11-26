# shared/s3_state

Creates the bucket that holds the Terraform state of every other root module except `local/docker`: `shared/<root>/` for the account-wide roots and `<environment>/<root>/` for dev, staging and prod. `deploy/bootstrap.sh` applies it first, once, with your own credentials. The bucket does not exist yet on that apply, so the script gives the root a local backend through a temporary `backend_override.tf`, applies it, and then moves the state into the bucket it created (`terraform init -migrate-state`). Every later run uses the `backend "s3"` block in `state.tf` directly.
