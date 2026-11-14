#!/bin/bash
# First boot of the EC2 instance, run once by cloud-init. The ECS-optimized AMI starts the ECS
# agent itself, which only has to know the cluster to register the instance in. Tasks with
# their own network interface are kept away from the instance metadata, so they can only use
# the credentials of their task role.
# It is a Terraform template, not a script to run as it is: main.tf fills in its placeholders
# through templatefile(), and a dollar sign that bash should see before a brace is doubled.
cat >> /etc/ecs/ecs.config <<CONFIG
ECS_CLUSTER=${cluster_name}
ECS_AWSVPC_BLOCK_IMDS=true
CONFIG
