# Database subnet group declaration (private subnets in at least 2 availability zones, which Multi-AZ needs)
resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = var.subnet_ids
}

# Database security group declaration (no rules here, the module of every client adds an ingress rule for itself)
resource "aws_security_group" "this" {
  name        = "${var.name}-database"
  description = "Security group of the RDS instance"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name}-database"
  }
}

# RDS PostgreSQL instance declaration (lives in the private subnets, multi_az adds a standby in another availability zone)
# RDS creates the master password itself and keeps it in a Secrets Manager secret which it rotates,
# the server reads that secret for every new connection
resource "aws_db_instance" "this" {
  identifier     = var.name
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage
  storage_type      = var.storage_type
  storage_encrypted = true

  db_name                     = var.db_name
  username                    = var.username
  manage_master_user_password = true
  port                        = var.port

  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  publicly_accessible    = false

  backup_retention_period = var.backup_retention_period
  skip_final_snapshot     = var.skip_final_snapshot
  deletion_protection     = var.deletion_protection
}
