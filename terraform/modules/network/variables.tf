variable "name" {
  description = "Name prefix applied to every network resource."
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for the VPC. Subnets are carved from it with cidrsubnet()."
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones (public and private subnet pairs)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be between 2 and 3."
  }
}

variable "container_port" {
  description = "Port the application container listens on. Only the ALB security group may reach it."
  type        = number
  default     = 8080
}

variable "tags" {
  description = "Tags merged into every taggable resource."
  type        = map(string)
  default     = {}
}
