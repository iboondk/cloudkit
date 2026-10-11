variable "name" {
  description = "Name prefix for observability resources. Also the dashboard name."
  type        = string
}

variable "aws_region" {
  description = "AWS region used by the dashboard metric widgets."
  type        = string
}

variable "alb_arn_suffix" {
  description = "ARN suffix of the ALB (LoadBalancer dimension)."
  type        = string
}

variable "target_group_arn_suffix" {
  description = "ARN suffix of the target group (TargetGroup dimension)."
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster (ClusterName dimension)."
  type        = string
}

variable "ecs_service_name" {
  description = "Name of the ECS service (ServiceName dimension)."
  type        = string
}

variable "db_instance_id" {
  description = "Identifier of the RDS instance (DBInstanceIdentifier dimension)."
  type        = string
}

variable "alarm_email" {
  description = "Email address subscribed to the alarm SNS topic. Empty string means no subscription."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags merged into every taggable resource."
  type        = map(string)
  default     = {}
}
