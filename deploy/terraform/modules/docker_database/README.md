# docker_database

PostgreSQL for local development, used in place of RDS. It runs in a Docker container on a bridge network of its own and is published on `published_address` only. The `vela47` user and database are fixed by the image in `deploy/images/local/database`. The password is generated here and passed to the container as `POSTGRES_PASSWORD`.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.10 |
| <a name="requirement_docker"></a> [docker](#requirement\_docker) | 4.7.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | 3.9.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_docker"></a> [docker](#provider\_docker) | 4.7.0 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.9.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [docker_container.this](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/container) | resource |
| [docker_image.this](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/image) | resource |
| [docker_network.this](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/network) | resource |
| [docker_volume.this](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs/resources/volume) | resource |
| [random_password.this](https://registry.terraform.io/providers/hashicorp/random/3.9.1/docs/resources/password) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_container_address"></a> [container\_address](#input\_container\_address) | Address of the database container on its network, the server connects to it | `string` | n/a | yes |
| <a name="input_health_check_interval"></a> [health\_check\_interval](#input\_health\_check\_interval) | Time between two health checks of the container | `string` | `"2s"` | no |
| <a name="input_health_check_retries"></a> [health\_check\_retries](#input\_health\_check\_retries) | Failed health checks in a row after which the container is unhealthy | `number` | `3` | no |
| <a name="input_health_check_start_period"></a> [health\_check\_start\_period](#input\_health\_check\_start\_period) | Time PostgreSQL gets to start before failed health checks count | `string` | `"1m"` | no |
| <a name="input_health_check_timeout"></a> [health\_check\_timeout](#input\_health\_check\_timeout) | Time one health check of the container may take | `string` | `"5s"` | no |
| <a name="input_image_context"></a> [image\_context](#input\_image\_context) | Absolute path of the directory the database image is built from | `string` | n/a | yes |
| <a name="input_name"></a> [name](#input\_name) | Prefix of the name of the network, image, volume and container | `string` | n/a | yes |
| <a name="input_network_gateway"></a> [network\_gateway](#input\_network\_gateway) | Gateway of the database network, clients on other networks reach the database through it | `string` | n/a | yes |
| <a name="input_network_subnet"></a> [network\_subnet](#input\_network\_subnet) | Subnet of the database network | `string` | n/a | yes |
| <a name="input_password_length"></a> [password\_length](#input\_password\_length) | Length of the password of the vela47 user on PostgreSQL | `number` | `32` | no |
| <a name="input_published_address"></a> [published\_address](#input\_published\_address) | Host address PostgreSQL is published on, 127.0.0.1 keeps it off the LAN | `string` | n/a | yes |
| <a name="input_published_port"></a> [published\_port](#input\_published\_port) | Port PostgreSQL is published on, clients still connect to the container's 5432 | `number` | n/a | yes |
| <a name="input_stop_timeout"></a> [stop\_timeout](#input\_stop\_timeout) | Seconds PostgreSQL gets to shut down when its container is stopped or destroyed | `number` | `30` | no |
| <a name="input_wait_timeout"></a> [wait\_timeout](#input\_wait\_timeout) | Seconds Terraform waits for the container to become healthy | `number` | `120` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_container_address"></a> [container\_address](#output\_container\_address) | Address of the database container on its network |
| <a name="output_password"></a> [password](#output\_password) | Password of the vela47 user on PostgreSQL |
<!-- END_TF_DOCS -->
