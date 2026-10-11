variable "aws_region" {
  description = "AWS region for the state bucket and IAM resources."
  type        = string
  default     = "us-east-1"
}

variable "github_owner" {
  description = "GitHub user or organization that owns the repository. No default; set it in terraform.tfvars."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name trusted by the OIDC roles."
  type        = string
  default     = "p2-cloudkit"
}

variable "state_bucket_name" {
  description = "Globally unique name for the Terraform state bucket. No default; set it in terraform.tfvars."
  type        = string
}
