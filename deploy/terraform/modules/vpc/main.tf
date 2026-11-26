# Availability zones declaration (read only)
data "aws_availability_zones" "available" {
  state = "available"

  #checkov:skip=CKV_AWS_394:Subnets take the first zones by name, a zone AWS adds later sorts after them
}

# VPC declaration
resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = var.name
  }

  #checkov:skip=CKV2_AWS_11:Flow logs are billed per GB, the security groups already log nothing in and the sandbox nothing out
}

# Internet gateway declaration (internet access for the public subnets)
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = var.name
  }
}

# Subnet declarations, one public and one private per availability zone
# Public subnets hold the load balancer and the NAT gateway, private subnets everything else
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidr_blocks)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.public_subnet_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.name}-public-${data.aws_availability_zones.available.names[count.index]}"
  }
}

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidr_blocks)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidr_blocks[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.name}-private-${data.aws_availability_zones.available.names[count.index]}"
  }
}

# Public route table declaration (all outbound traffic goes to the internet gateway)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${var.name}-public"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT declarations (outbound only internet access for the private subnets, a single NAT in the first zone)
# A NAT gateway is managed and highly available within its zone; a NAT instance is a t4g.nano that costs a tenth
# of it and is enough for an environment nobody depends on
resource "aws_eip" "this" {
  domain = "vpc"

  tags = {
    Name = "${var.name}-nat"
  }
}

resource "aws_nat_gateway" "this" {
  count = var.nat_type == "gateway" ? 1 : 0

  allocation_id = aws_eip.this.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = var.name
  }

  # NAT gateway needs the internet gateway, Terraform can not see this by itself
  depends_on = [aws_internet_gateway.this]
}

data "aws_ssm_parameter" "nat_instance_ami" {
  count = var.nat_type == "instance" ? 1 : 0

  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_security_group" "nat_instance" {
  count = var.nat_type == "instance" ? 1 : 0

  name        = "${var.name}-nat-instance"
  description = "NAT instance, forwards what the private subnets send to the internet"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name}-nat-instance"
  }
}

resource "aws_vpc_security_group_ingress_rule" "nat_instance_from_private" {
  count = var.nat_type == "instance" ? length(var.private_subnet_cidr_blocks) : 0

  security_group_id = aws_security_group.nat_instance[0].id
  description       = "Traffic of a private subnet on its way out"
  cidr_ipv4         = var.private_subnet_cidr_blocks[count.index]
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "nat_instance_all" {
  count = var.nat_type == "instance" ? 1 : 0

  security_group_id = aws_security_group.nat_instance[0].id
  description       = "Forwarded traffic and the packages of the instance itself"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# The instance forwards and masquerades everything the private subnets send, so it must not check that a packet is its own
resource "aws_instance" "nat" {
  count = var.nat_type == "instance" ? 1 : 0

  ami                    = data.aws_ssm_parameter.nat_instance_ami[0].value
  instance_type          = var.nat_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.nat_instance[0].id]
  source_dest_check      = false
  monitoring             = false

  # The address it boots with lets user_data install iptables before the elastic address is moved onto it
  associate_public_ip_address = true

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y iptables-services
    echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/90-nat.conf
    sysctl -p /etc/sysctl.d/90-nat.conf
    interface=$(ip route show default | awk '{print $5}')
    iptables -t nat -A POSTROUTING -o "$interface" -j MASQUERADE
    iptables -F FORWARD
    service iptables save
    systemctl enable --now iptables
  EOT

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${var.name}-nat"
  }

  # A newer AMI would replace the instance and cut the private subnets off on an unrelated apply
  lifecycle {
    ignore_changes = [ami]
  }

  #checkov:skip=CKV_AWS_126:Detailed monitoring is billed per metric and the instance only forwards packets
  #checkov:skip=CKV_AWS_135:t4g instances are EBS optimized by default
  #checkov:skip=CKV2_AWS_41:The instance calls no AWS API, so it has no IAM role
  #checkov:skip=CKV_AWS_88:A NAT instance needs a public address, its security group takes traffic from the private subnets only
}

resource "aws_eip_association" "nat_instance" {
  count = var.nat_type == "instance" ? 1 : 0

  allocation_id = aws_eip.this.id
  instance_id   = aws_instance.nat[0].id
}

# Private route table declaration (all outbound traffic goes to the NAT)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name}-private"
  }
}

resource "aws_route" "private_nat_gateway" {
  count = var.nat_type == "gateway" ? 1 : 0

  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[0].id
}

resource "aws_route" "private_nat_instance" {
  count = var.nat_type == "instance" ? 1 : 0

  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = aws_instance.nat[0].primary_network_interface_id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# S3 gateway endpoint (free; image layers pulled from ECR are stored in S3 and skip the NAT)
data "aws_region" "current" {}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]

  tags = {
    Name = "${var.name}-s3"
  }
}

# The default security group of the VPC allows nothing, every resource uses a security group of its own
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name}-default"
  }
}
