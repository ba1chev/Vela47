# app

The Vela47 server in one AWS environment. Everything the application owns lives in this module, and it is laid out in these files:

- `main.tf`: the ECS cluster, its capacity provider over an auto scaling group of Graviton instances, and the server task definition and service
- `load_balancer.tf` and `dns.tf`: the ALB with HTTP → HTTPS, the blue and green target groups behind one listener rule, its ACM certificate and the Route 53 alias record
- `alarms.tf`: the alarms that roll a deployment back (5xx answers, unhealthy tasks)
- `sandbox.tf`: the Lambda function that runs model-written code. Its security group allows no traffic and its role has no AWS permissions
- `iam.tf`, `security_groups.tf` and `secrets.tf`: the roles, all under `permissions_boundary_arn`, the traffic rules (including the ingress rule on the database security group) and the application secret

The module builds nothing. The images of a release are built once by the delivery workflow, pushed to the shared ECR repositories, and passed in by digest (`app_image`, `sandbox_image`).

`deployment_strategy` is `ROLLING` (new tasks beside the old ones, circuit breaker) or `CANARY` (ECS blue/green: a full set of new tasks in the idle target group, `canary_percent` of the traffic, then all of it, the old tasks kept for `bake_time_minutes`). Both roll back on the alarms. After a canary deployment ECS serves from the other target group, so the load balancer of the service and the weights of the listener rule are ignored by Terraform; switching the strategy needs `terraform apply -replace=module.app.aws_ecs_service.this`.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
