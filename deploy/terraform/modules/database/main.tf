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

  #checkov:skip=CKV2_AWS_5:The instance below uses it, checkov does not follow the reference
}

# RDS PostgreSQL instance declaration (lives in the private subnets, multi_az adds a standby in another availability zone)
# RDS creates the master password itself and keeps it in a Secrets Manager secret which it rotates,
# the server reads that secret for every new connection. Backups are kept for backup_retention_period days, so the
# database can be restored to any second in that time; a deployment also takes a manual snapshot before it migrates
# the schema in staging and prod, and destroying the instance there leaves a final snapshot
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

  backup_retention_period    = var.backup_retention_period
  backup_window              = var.backup_window
  maintenance_window         = var.maintenance_window
  copy_tags_to_snapshot      = true
  auto_minor_version_upgrade = true
  skip_final_snapshot        = var.skip_final_snapshot
  final_snapshot_identifier  = var.skip_final_snapshot ? null : "${var.name}-final"
  deletion_protection        = var.deletion_protection

  #checkov:skip=CKV_AWS_161:The server authenticates with the RDS-managed password from Secrets Manager
  #checkov:skip=CKV_AWS_118:Enhanced monitoring is billed per instance, the CloudWatch metrics of RDS are enough here
  #checkov:skip=CKV_AWS_129:Log exports are billed per GB in CloudWatch, the logs stay readable in the RDS console
  #checkov:skip=CKV_AWS_353:Performance Insights is not needed at the size of this database
  #checkov:skip=CKV2_AWS_30:Query logging is not needed at the size of this database
  #checkov:skip=CKV_AWS_293:Deletion protection is a variable, on in staging and prod, off in dev so it can be torn down
  #checkov:skip=CKV_AWS_157:Multi-AZ is a variable, on in staging and prod, off in dev to keep it cheap
}
