resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, { Name = "${var.name}-db-subnets" })
}

# The master password is generated and stored by RDS in Secrets Manager
# (manage_master_user_password), so no password appears in code, tfvars or state.
resource "aws_db_instance" "this" {
  identifier = "${var.name}-pg"

  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.username

  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.db_security_group_id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = var.deletion_protection

  performance_insights_enabled = false
  auto_minor_version_upgrade   = true
  apply_immediately            = true

  tags = merge(var.tags, { Name = "${var.name}-pg" })
}
