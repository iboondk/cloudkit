variable "name" {
  description = "Name prefix for edge resources. Also used as the CloudFront distribution comment."
  type        = string
}

variable "alb_dns_name" {
  description = "DNS name of the ALB, used as the default (dynamic) CloudFront origin."
  type        = string
}

variable "price_class" {
  description = "CloudFront price class. PriceClass_100 covers North America and Europe only."
  type        = string
  default     = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class must be PriceClass_100, PriceClass_200 or PriceClass_All."
  }
}

variable "tags" {
  description = "Tags merged into every taggable resource."
  type        = map(string)
  default     = {}
}
