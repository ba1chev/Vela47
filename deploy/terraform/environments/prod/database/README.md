# prod/database

PostgreSQL on RDS in the private subnets of the `vpc` root module. It is Single-AZ by default; set `multi_az = true` to add a standby. The `app` root module reads its outputs and adds the ingress rule for the server task to its security group.

Order: apply after `vpc` and before `app`. Destroy after `app` and before `vpc`.
