# app

The Vela47 server in production. Everything the application owns lives in this module, and it is laid out in these files:

- `main.tf`: the ECS cluster, the single Graviton EC2 instance (launch template and auto scaling group), and the server task definition and service
- `load_balancer.tf` and `dns.tf`: the ALB with HTTP → HTTPS, its ACM certificate, and the Route 53 alias record
- `ecr.tf`: the two ECR repositories, plus the server and sandbox images. Terraform builds both images on this machine for arm64 and pushes them
- `sandbox.tf`: the Lambda function that runs model-written code. Its security group allows no traffic and its role has no AWS permissions
- `iam.tf`, `security_groups.tf` and `secrets.tf`: the roles, the traffic rules (including the ingress rule on the database security group) and the application secret

The calling root module must configure the `docker` provider with ECR credentials. Docker has to be running during `apply`.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.10 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |
| <a name="requirement_docker"></a> [docker](#requirement\_docker) | 4.7.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | 3.9.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 6.0 |
| <a name="provider_docker"></a> [docker](#provider\_docker) | 4.7.0 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.9.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_acm_certificate.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate) | resource |
| [aws_acm_certificate_validation.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation) | resource |
| [aws_autoscaling_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_group) | resource |
| [aws_cloudwatch_log_group.app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.sandbox](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_ecr_lifecycle_policy.app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_lifecycle_policy) | resource |
| [aws_ecr_lifecycle_policy.sandbox](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_lifecycle_policy) | resource |
| [aws_ecr_repository.app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository) | resource |
| [aws_ecr_repository.sandbox](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository) | resource |
| [aws_ecs_cluster.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_cluster) | resource |
| [aws_ecs_service.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service) | resource |
| [aws_ecs_task_definition.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition) | resource |
| [aws_iam_instance_profile.instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_instance_profile) | resource |
| [aws_iam_role.instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.sandbox](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.task_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy_attachment.instance_container_service](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.instance_session_manager](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.sandbox_vpc_access](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.task_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_function.sandbox](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_launch_template.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/launch_template) | resource |
| [aws_lb.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb) | resource |
| [aws_lb_listener.http](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) | resource |
| [aws_lb_listener.https](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) | resource |
| [aws_lb_target_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group) | resource |
| [aws_route53_record.app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.certificate_validation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_secretsmanager_secret.app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.app](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version) | resource |
| [aws_security_group.instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.load_balancer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.sandbox](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_vpc_security_group_egress_rule.instance_all](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_egress_rule.load_balancer_all](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_egress_rule.task_all](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.database_from_task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.load_balancer_http](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.load_balancer_https](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.task_from_load_balancer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [docker_image.app](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/image) | resource |
| [docker_image.sandbox](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/image) | resource |
| [docker_registry_image.app](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/registry_image) | resource |
| [docker_registry_image.sandbox](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/registry_image) | resource |
| [random_password.admin_password](https://registry.terraform.io/providers/hashicorp/random/3.9.1/docs/resources/password) | resource |
| [random_password.token_secret](https://registry.terraform.io/providers/hashicorp/random/3.9.1/docs/resources/password) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.instance_assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.sandbox_assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.task_assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_route53_zone.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/route53_zone) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_admin_password_length"></a> [admin\_password\_length](#input\_admin\_password\_length) | Length of the password of the admin bootstrapped on the first start | `number` | `24` | no |
| <a name="input_admin_username"></a> [admin\_username](#input\_admin\_username) | Username of the admin bootstrapped on the first start | `string` | n/a | yes |
| <a name="input_app_dockerfile"></a> [app\_dockerfile](#input\_app\_dockerfile) | Dockerfile of the server image, relative to repository\_path | `string` | `"deploy/images/prod/app/Dockerfile"` | no |
| <a name="input_bedrock_model_ids"></a> [bedrock\_model\_ids](#input\_bedrock\_model\_ids) | Bedrock models the server task may call, an eu. prefix is a cross-region inference profile | `list(string)` | n/a | yes |
| <a name="input_container_name"></a> [container\_name](#input\_container\_name) | Name of the server container in the task definition | `string` | `"app"` | no |
| <a name="input_container_port"></a> [container\_port](#input\_container\_port) | Port the server listens on in the container, the load balancer forwards to it | `number` | `8000` | no |
| <a name="input_database_address"></a> [database\_address](#input\_database\_address) | Host name of the RDS instance, VELA47\_DATABASE\_HOST | `string` | n/a | yes |
| <a name="input_database_name"></a> [database\_name](#input\_database\_name) | Database on the RDS instance, VELA47\_DATABASE\_NAME | `string` | n/a | yes |
| <a name="input_database_port"></a> [database\_port](#input\_database\_port) | Port of the RDS instance, VELA47\_DATABASE\_PORT | `number` | n/a | yes |
| <a name="input_database_secret_arn"></a> [database\_secret\_arn](#input\_database\_secret\_arn) | ARN of the RDS-managed secret with the database username and password, VELA47\_DATABASE\_SECRET\_ID | `string` | n/a | yes |
| <a name="input_database_security_group_id"></a> [database\_security\_group\_id](#input\_database\_security\_group\_id) | Security group of the RDS instance, the server task adds its ingress rule to it | `string` | n/a | yes |
| <a name="input_domain_name"></a> [domain\_name](#input\_domain\_name) | Domain the application is served on over HTTPS | `string` | n/a | yes |
| <a name="input_ecr_kept_images"></a> [ecr\_kept\_images](#input\_ecr\_kept\_images) | How many images each ECR repository keeps, older ones are deleted | `number` | `5` | no |
| <a name="input_instance_ami"></a> [instance\_ami](#input\_instance\_ami) | AMI of the EC2 instances, the ECS-optimized Amazon Linux 2023 for arm64 comes with Docker and the ECS agent | `string` | `"resolve:ssm:/aws/service/ecs/optimized-ami/amazon-linux-2023/arm64/recommended/image_id"` | no |
| <a name="input_instance_desired_count"></a> [instance\_desired\_count](#input\_instance\_desired\_count) | Desired number of EC2 instances running | `number` | `1` | no |
| <a name="input_instance_health_check_grace_period"></a> [instance\_health\_check\_grace\_period](#input\_instance\_health\_check\_grace\_period) | Seconds a new instance gets before failed health checks count, the ECS-optimized AMI only has to start the ECS agent | `number` | `300` | no |
| <a name="input_instance_max_count"></a> [instance\_max\_count](#input\_instance\_max\_count) | Maximum number of EC2 instances running | `number` | `1` | no |
| <a name="input_instance_metadata_hop_limit"></a> [instance\_metadata\_hop\_limit](#input\_instance\_metadata\_hop\_limit) | How many network hops the instance metadata (IMDSv2) answers reach, 1 is enough since the ECS agent uses the host network and tasks get their credentials from ECS | `number` | `1` | no |
| <a name="input_instance_min_count"></a> [instance\_min\_count](#input\_instance\_min\_count) | Minimum number of EC2 instances running | `number` | `1` | no |
| <a name="input_instance_root_device_name"></a> [instance\_root\_device\_name](#input\_instance\_root\_device\_name) | Root device name of the AMI | `string` | `"/dev/xvda"` | no |
| <a name="input_instance_root_volume_size"></a> [instance\_root\_volume\_size](#input\_instance\_root\_volume\_size) | Size of the root volume in GB, it holds the image of the server task | `number` | `30` | no |
| <a name="input_instance_type"></a> [instance\_type](#input\_instance\_type) | Type of the EC2 instances, it has to be a Graviton (arm64) type, and fit the server task and a second one during a deploy | `string` | n/a | yes |
| <a name="input_load_balancer_deletion_protection"></a> [load\_balancer\_deletion\_protection](#input\_load\_balancer\_deletion\_protection) | Protects the load balancer from deletion (true for real production) | `bool` | `false` | no |
| <a name="input_load_balancer_deregistration_delay"></a> [load\_balancer\_deregistration\_delay](#input\_load\_balancer\_deregistration\_delay) | Seconds the load balancer lets requests to a stopping task finish | `number` | `30` | no |
| <a name="input_load_balancer_health_check_path"></a> [load\_balancer\_health\_check\_path](#input\_load\_balancer\_health\_check\_path) | Path the load balancer checks the server tasks on | `string` | `"/"` | no |
| <a name="input_load_balancer_idle_timeout"></a> [load\_balancer\_idle\_timeout](#input\_load\_balancer\_idle\_timeout) | Seconds a connection may stay idle, an agent run streams for minutes and an upload is embedded before it returns | `number` | `300` | no |
| <a name="input_load_balancer_ingress_cidr_ipv4"></a> [load\_balancer\_ingress\_cidr\_ipv4](#input\_load\_balancer\_ingress\_cidr\_ipv4) | CIDR the load balancer takes HTTP and HTTPS traffic from | `string` | `"0.0.0.0/0"` | no |
| <a name="input_load_balancer_ssl_policy"></a> [load\_balancer\_ssl\_policy](#input\_load\_balancer\_ssl\_policy) | TLS policy of the HTTPS listener | `string` | `"ELBSecurityPolicy-TLS13-1-2-2021-06"` | no |
| <a name="input_log_retention_days"></a> [log\_retention\_days](#input\_log\_retention\_days) | Days the logs of the server task and of the sandbox function are kept | `number` | `14` | no |
| <a name="input_name"></a> [name](#input\_name) | Prefix of the name of every resource of the application | `string` | n/a | yes |
| <a name="input_private_subnet_ids"></a> [private\_subnet\_ids](#input\_private\_subnet\_ids) | Private subnets of the EC2 instance, the server task and the sandbox function | `list(string)` | n/a | yes |
| <a name="input_public_subnet_ids"></a> [public\_subnet\_ids](#input\_public\_subnet\_ids) | Public subnets of the load balancer | `list(string)` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | AWS region the server reads its secrets and calls the models in | `string` | n/a | yes |
| <a name="input_repository_path"></a> [repository\_path](#input\_repository\_path) | Absolute path of the repository root, the context the server image is built from | `string` | n/a | yes |
| <a name="input_sandbox_context"></a> [sandbox\_context](#input\_sandbox\_context) | Directory the sandbox function image is built from, relative to repository\_path | `string` | `"deploy/images/prod/sandbox"` | no |
| <a name="input_sandbox_function_name"></a> [sandbox\_function\_name](#input\_sandbox\_function\_name) | Name of the Lambda function the TEST subagent runs its commands in, the server calls it by this name | `string` | n/a | yes |
| <a name="input_sandbox_memory_size"></a> [sandbox\_memory\_size](#input\_sandbox\_memory\_size) | Memory of the sandbox function in MB, the same limit a sandbox container has in development | `number` | `512` | no |
| <a name="input_sandbox_timeout"></a> [sandbox\_timeout](#input\_sandbox\_timeout) | Seconds the sandbox function may run, a command gets 60 and the rest is for copying the workspace in | `number` | `90` | no |
| <a name="input_secret_recovery_window_in_days"></a> [secret\_recovery\_window\_in\_days](#input\_secret\_recovery\_window\_in\_days) | Days a deleted application secret can still be restored, 0 deletes it at once so the name is free for the next apply | `number` | `0` | no |
| <a name="input_task_cpu"></a> [task\_cpu](#input\_task\_cpu) | CPU units the server container reserves (1024 is one vCPU) | `number` | `1024` | no |
| <a name="input_task_desired_count"></a> [task\_desired\_count](#input\_task\_desired\_count) | Number of server tasks running | `number` | `1` | no |
| <a name="input_task_health_check_grace_period"></a> [task\_health\_check\_grace\_period](#input\_task\_health\_check\_grace\_period) | Seconds a new server task gets before failed load balancer health checks count | `number` | `60` | no |
| <a name="input_task_memory"></a> [task\_memory](#input\_task\_memory) | Memory limit of the server container in MiB, the task is stopped beyond it | `number` | `1536` | no |
| <a name="input_task_memory_reservation"></a> [task\_memory\_reservation](#input\_task\_memory\_reservation) | Memory in MiB reserved for the server container on the instance, two tasks have to fit during a deploy | `number` | `768` | no |
| <a name="input_tavily_api_key"></a> [tavily\_api\_key](#input\_tavily\_api\_key) | Key of the Tavily search API the server searches the web with, empty falls back to DuckDuckGo | `string` | `""` | no |
| <a name="input_token_secret_length"></a> [token\_secret\_length](#input\_token\_secret\_length) | Length of the key which signs the session tokens | `number` | `48` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC every resource of the application lives in | `string` | n/a | yes |
| <a name="input_zone_name"></a> [zone\_name](#input\_zone\_name) | Route 53 hosted zone which already exists in the account and holds domain\_name | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_admin_password"></a> [admin\_password](#output\_admin\_password) | Password of the admin bootstrapped on the first start |
| <a name="output_admin_username"></a> [admin\_username](#output\_admin\_username) | Username of the admin bootstrapped on the first start |
| <a name="output_autoscaling_group_name"></a> [autoscaling\_group\_name](#output\_autoscaling\_group\_name) | Name of the auto scaling group which runs the EC2 instance of the cluster |
| <a name="output_cloudwatch_log_group_app_name"></a> [cloudwatch\_log\_group\_app\_name](#output\_cloudwatch\_log\_group\_app\_name) | Name of the log group of the server task |
| <a name="output_ecr_image_app_uri"></a> [ecr\_image\_app\_uri](#output\_ecr\_image\_app\_uri) | URI of the server image the task runs, pinned by digest |
| <a name="output_ecs_cluster_name"></a> [ecs\_cluster\_name](#output\_ecs\_cluster\_name) | Name of the ECS cluster |
| <a name="output_ecs_service_name"></a> [ecs\_service\_name](#output\_ecs\_service\_name) | Name of the ECS service of the server task |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | Name of the Lambda function the TEST subagent runs its commands in |
| <a name="output_lb_dns_name"></a> [lb\_dns\_name](#output\_lb\_dns\_name) | DNS name of the load balancer, the target of the application domain |
| <a name="output_lb_target_group_arn"></a> [lb\_target\_group\_arn](#output\_lb\_target\_group\_arn) | ARN of the target group of the server tasks |
| <a name="output_route53_record_fqdn"></a> [route53\_record\_fqdn](#output\_route53\_record\_fqdn) | Domain the application is served on over HTTPS |
| <a name="output_secretsmanager_secret_app_arn"></a> [secretsmanager\_secret\_app\_arn](#output\_secretsmanager\_secret\_app\_arn) | ARN of the application secret with the token signing key and the bootstrapped admin, VELA47\_APP\_SECRET\_ID |
<!-- END_TF_DOCS -->
