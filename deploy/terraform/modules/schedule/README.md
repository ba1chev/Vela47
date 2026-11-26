# schedule

Office hours for an environment nobody uses at night, which is how dev stays cheap. EventBridge Scheduler sets the task count of the server service to 0 at 20:00 on weekdays and stops the database ten minutes later; it starts the database at 07:30 and sets the task count back at 08:00. With no tasks to place, the ECS capacity provider scales the instances to 0, so a night or a weekend costs only the load balancer, the NAT instance and the storage.

A deployment at night still works: the deployment workflow starts a stopped database before it applies, and Terraform sets the task count back. RDS starts a database by itself after it has been stopped for seven days, which the weekday schedule never reaches.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
