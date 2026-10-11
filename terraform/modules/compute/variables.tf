variable "name" {
  description = "Name prefix for compute resources. Also the ECS task family."
  type        = string
}

variable "aws_region" {
  description = "AWS region, used by the awslogs log driver."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for the target group."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB and the Fargate tasks (public IP, no NAT)."
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for the ALB."
  type        = string
}

variable "app_security_group_id" {
  description = "Security group ID for the app tasks."
  type        = string
}

variable "container_image" {
  description = "OCI image for the Tenantly API container."
  type        = string
}

variable "container_port" {
  description = "Port the application container listens on."
  type        = number
  default     = 8080
}

variable "health_check_path" {
  description = "HTTP path the ALB uses for target health checks. Must return 200."
  type        = string
  default     = "/healthz"
}

variable "cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)."
  type        = number
  default     = 256
}

variable "memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Number of running tasks in the ECS service."
  type        = number
  default     = 1
}

variable "redis_image" {
  description = "Redis sidecar image. Runs in the same task and listens on localhost:6379."
  type        = string
  default     = "public.ecr.aws/docker/library/redis:7-alpine"
}

variable "db_address" {
  description = "PostgreSQL hostname, passed to the app as DB_HOST."
  type        = string
}

variable "db_port" {
  description = "PostgreSQL port, passed to the app as DB_PORT."
  type        = number
}

variable "db_name" {
  description = "PostgreSQL database name, passed to the app as DB_NAME."
  type        = string
}

variable "db_secret_arn" {
  description = "ARN of the RDS-managed secret. The app reads username and password keys from it."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags merged into every taggable resource."
  type        = map(string)
  default     = {}
}
