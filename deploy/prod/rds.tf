# Database subnet group declaration (subnets in 2 availability zones, which Multi-AZ needs once it is turned on)
resource "aws_db_subnet_group" "database" {
  name       = var.rds_subnet_group_name
  subnet_ids = aws_subnet.private[*].id
  tags       = local.common_tags
}

# RDS PostgreSQL instance declaration (lives in the private subnets, rds_multi_az adds a standby in another availability zone)
# RDS creates the master password itself and keeps it in a Secrets Manager secret which it rotates,
# the server reads that secret for every new connection
resource "aws_db_instance" "database" {
  identifier     = var.rds_instance_identifier
  engine         = var.rds_engine
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class

  allocated_storage = var.rds_allocated_storage
  storage_type      = var.rds_storage_type
  storage_encrypted = var.rds_storage_encrypted

  db_name                     = var.rds_database_name
  username                    = var.rds_master_username
  manage_master_user_password = true
  port                        = var.rds_port

  multi_az               = var.rds_multi_az
  db_subnet_group_name   = aws_db_subnet_group.database.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = var.rds_publicly_accessible

  backup_retention_period = var.rds_backup_retention_period
  skip_final_snapshot     = var.rds_skip_final_snapshot
  deletion_protection     = var.rds_deletion_protection
  tags                    = local.common_tags
}
