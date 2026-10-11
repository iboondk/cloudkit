variable "aws_region" {
  description = "AWS region for every resource in the dev stack."
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Name prefix for the dev stack."
  type        = string
  default     = "cloudkit-dev"
}

variable "container_image" {
  description = "OCI image for the application container. Placeholder until the Tenantly image is published."
  type        = string
  default     = "public.ecr.aws/nginx/nginx:stable"
}

variable "alarm_email" {
  description = "Email subscribed to the alarm SNS topic. Empty string means no subscription."
  type        = string
  default     = ""
}
