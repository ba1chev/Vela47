# database

PostgreSQL on RDS in the private subnets of a VPC. RDS creates the master password, keeps it in a Secrets Manager secret and rotates it. The server reads that secret for every new connection.

The security group has no rules of its own. Each client adds an ingress rule from its own security group to `security_group_id`, so this module does not need to know who its clients are.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.10 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 6.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_db_instance.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance) | resource |
| [aws_db_subnet_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_subnet_group) | resource |
| [aws_security_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_allocated_storage"></a> [allocated\_storage](#input\_allocated\_storage) | Storage of the RDS instance in GB | `number` | `20` | no |
| <a name="input_backup_retention_period"></a> [backup\_retention\_period](#input\_backup\_retention\_period) | Days the automated backups of the RDS instance are kept | `number` | `7` | no |
| <a name="input_db_name"></a> [db\_name](#input\_db\_name) | Database created on the RDS instance, the same name the server uses by default | `string` | `"vela47"` | no |
| <a name="input_deletion_protection"></a> [deletion\_protection](#input\_deletion\_protection) | Protects the RDS instance from deletion (true for real production) | `bool` | `false` | no |
| <a name="input_engine_version"></a> [engine\_version](#input\_engine\_version) | Major version of PostgreSQL, the same as the database container in development | `string` | `"17"` | no |
| <a name="input_instance_class"></a> [instance\_class](#input\_instance\_class) | Instance class of the RDS instance | `string` | `"db.t4g.micro"` | no |
| <a name="input_multi_az"></a> [multi\_az](#input\_multi\_az) | Whether a standby replica runs in another availability zone (true for real production, it doubles the price of the database) | `bool` | `false` | no |
| <a name="input_name"></a> [name](#input\_name) | Identifier of the RDS instance, also the name of its subnet group and security group | `string` | n/a | yes |
| <a name="input_port"></a> [port](#input\_port) | Port of the RDS instance, the server uses 5432 by default | `number` | `5432` | no |
| <a name="input_skip_final_snapshot"></a> [skip\_final\_snapshot](#input\_skip\_final\_snapshot) | Whether the RDS instance is deleted without a final snapshot (false for real production) | `bool` | `true` | no |
| <a name="input_storage_type"></a> [storage\_type](#input\_storage\_type) | Storage type of the RDS instance | `string` | `"gp3"` | no |
| <a name="input_subnet_ids"></a> [subnet\_ids](#input\_subnet\_ids) | Private subnets of the subnet group, in at least 2 availability zones | `list(string)` | n/a | yes |
| <a name="input_username"></a> [username](#input\_username) | Master user of the RDS instance, its password is created and rotated by RDS in Secrets Manager | `string` | `"vela47"` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC the security group of the instance is created in | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_db_instance_address"></a> [db\_instance\_address](#output\_db\_instance\_address) | Host name of the RDS instance, it follows the primary through a failover |
| <a name="output_db_instance_master_user_secret_arn"></a> [db\_instance\_master\_user\_secret\_arn](#output\_db\_instance\_master\_user\_secret\_arn) | ARN of the RDS-managed secret with the username and password of the master user |
| <a name="output_db_instance_name"></a> [db\_instance\_name](#output\_db\_instance\_name) | Database created on the RDS instance |
| <a name="output_db_instance_port"></a> [db\_instance\_port](#output\_db\_instance\_port) | Port of the RDS instance |
| <a name="output_security_group_id"></a> [security\_group\_id](#output\_security\_group\_id) | ID of the security group of the RDS instance, clients add their ingress rules to it |
<!-- END_TF_DOCS -->
