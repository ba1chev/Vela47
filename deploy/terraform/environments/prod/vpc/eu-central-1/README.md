# prod/vpc/eu-central-1

The production VPC in eu-central-1: public and private subnets in two availability zones, an internet gateway and a single NAT gateway. The `database` and `app` root modules read its outputs through `terraform_remote_state`, so apply this one before them and destroy it after them.
