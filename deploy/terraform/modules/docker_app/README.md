# docker_app

The Vela47 server for local development. It runs in a Docker container on a bridge network of its own and reaches the database through the gateways of the two networks.

- Ollama stays on the host and is reached through `host.docker.internal`.
- The sandbox containers are started through the host's Docker socket, so they run next to the server, not inside it. That socket gives the server full control of the local Docker, which is acceptable for development only.

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
| [random_password.admin_password](https://registry.terraform.io/providers/hashicorp/random/3.9.1/docs/resources/password) | resource |
| [random_password.token_secret](https://registry.terraform.io/providers/hashicorp/random/3.9.1/docs/resources/password) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_admin_password_length"></a> [admin\_password\_length](#input\_admin\_password\_length) | Length of the password of the admin bootstrapped on the first start | `number` | `24` | no |
| <a name="input_admin_username"></a> [admin\_username](#input\_admin\_username) | Username of the admin bootstrapped on the first start | `string` | n/a | yes |
| <a name="input_container_address"></a> [container\_address](#input\_container\_address) | Address of the application container on its network | `string` | n/a | yes |
| <a name="input_database_host"></a> [database\_host](#input\_database\_host) | Address of the database container, VELA47\_DATABASE\_HOST | `string` | n/a | yes |
| <a name="input_database_password"></a> [database\_password](#input\_database\_password) | Password of the vela47 user on the database, VELA47\_DATABASE\_PASSWORD | `string` | n/a | yes |
| <a name="input_dockerfile"></a> [dockerfile](#input\_dockerfile) | Dockerfile of the server image, relative to repository\_path | `string` | `"deploy/images/dev/app/Dockerfile"` | no |
| <a name="input_health_check_interval"></a> [health\_check\_interval](#input\_health\_check\_interval) | Time between two health checks of the container | `string` | `"5s"` | no |
| <a name="input_health_check_retries"></a> [health\_check\_retries](#input\_health\_check\_retries) | Failed health checks in a row after which the container is unhealthy | `number` | `3` | no |
| <a name="input_health_check_start_period"></a> [health\_check\_start\_period](#input\_health\_check\_start\_period) | Time the server gets to start, including bringing up the sandbox, before failed health checks count | `string` | `"5m"` | no |
| <a name="input_health_check_timeout"></a> [health\_check\_timeout](#input\_health\_check\_timeout) | Time one health check of the container may take | `string` | `"5s"` | no |
| <a name="input_name"></a> [name](#input\_name) | Prefix of the name of the network, image and container | `string` | n/a | yes |
| <a name="input_network_gateway"></a> [network\_gateway](#input\_network\_gateway) | Gateway of the application network | `string` | n/a | yes |
| <a name="input_network_subnet"></a> [network\_subnet](#input\_network\_subnet) | Subnet of the application network | `string` | n/a | yes |
| <a name="input_ollama_host"></a> [ollama\_host](#input\_ollama\_host) | URL of the Ollama server on the host, as the container reaches it | `string` | n/a | yes |
| <a name="input_published_address"></a> [published\_address](#input\_published\_address) | Host address the server and its UI are published on, 127.0.0.1 keeps them off the LAN | `string` | n/a | yes |
| <a name="input_published_port"></a> [published\_port](#input\_published\_port) | Port the server and its UI are published on | `number` | n/a | yes |
| <a name="input_repository_path"></a> [repository\_path](#input\_repository\_path) | Absolute path of the repository root, the context the server image is built from | `string` | n/a | yes |
| <a name="input_sandbox_directory"></a> [sandbox\_directory](#input\_sandbox\_directory) | Sandbox compose project copied into the server image, relative to repository\_path | `string` | `"deploy/images/dev/sandbox"` | no |
| <a name="input_stop_timeout"></a> [stop\_timeout](#input\_stop\_timeout) | Seconds the server gets to bring the sandbox down when its container is stopped or destroyed | `number` | `60` | no |
| <a name="input_token_secret_length"></a> [token\_secret\_length](#input\_token\_secret\_length) | Length of the key which signs the session tokens | `number` | `48` | no |
| <a name="input_wait_timeout"></a> [wait\_timeout](#input\_wait\_timeout) | Seconds Terraform waits for the container to become healthy | `number` | `600` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_admin_password"></a> [admin\_password](#output\_admin\_password) | Password of the admin bootstrapped on the first start |
| <a name="output_admin_username"></a> [admin\_username](#output\_admin\_username) | Username of the admin bootstrapped on the first start |
| <a name="output_url"></a> [url](#output\_url) | Where the UI is served |
<!-- END_TF_DOCS -->
