output "instance_id" {
  description = "Identifier of the RDS instance."
  value       = aws_db_instance.this.identifier
}

output "address" {
  description = "Hostname of the RDS instance (private)."
  value       = aws_db_instance.this.address
}

output "port" {
  description = "Port the PostgreSQL instance listens on."
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Name of the initial database."
  value       = aws_db_instance.this.db_name
}

output "master_user_secret_arn" {
  description = "ARN of the RDS-managed Secrets Manager secret holding the master credentials."
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}
