variable "name" {
  description = "Name prefix for database resources."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group (no internet route)."
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group ID for the database (PostgreSQL from the app SG only)."
  type        = string
}

variable "db_name" {
  description = "Name of the initial database created in the instance."
  type        = string
  default     = "tenantly"
}

variable "username" {
  description = "Master username. The password is generated and managed by RDS in Secrets Manager."
  type        = string
  default     = "tenantly"
}

variable "instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GiB (gp3)."
  type        = number
  default     = 20
}

variable "engine_version" {
  description = "PostgreSQL major version."
  type        = string
  default     = "16"
}

variable "deletion_protection" {
  description = "Protect the instance from deletion. Off by default so the dev stack can be torn down."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags merged into every taggable resource."
  type        = map(string)
  default     = {}
}
