# database

PostgreSQL on RDS in the private subnets of a VPC. RDS creates the master password, keeps it in a Secrets Manager secret and rotates it. The server reads that secret for every new connection.

Automated backups allow a point-in-time restore for `backup_retention_period` days. With `skip_final_snapshot = false` a destroy leaves the snapshot `<name>-final`. Minor versions are upgraded by RDS in `maintenance_window`.

The security group has no rules of its own. Each client adds an ingress rule from its own security group to `security_group_id`, so this module does not need to know who its clients are.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
