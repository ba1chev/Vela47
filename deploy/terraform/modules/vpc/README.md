# vpc

A VPC with one public and one private subnet per availability zone. The public subnets route to an internet gateway. The private subnets route to a single NAT in the first zone, which is cheaper than one per zone but is also a single point of failure. `nat_type` picks a managed NAT gateway or a `t4g.nano` NAT instance at a tenth of the price, enough for an environment nobody depends on. A free S3 gateway endpoint keeps image layers pulled from ECR off the NAT, and the default security group of the VPC allows nothing.

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
