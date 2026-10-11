# Partial backend configuration. Values come from backend.hcl (copy backend.hcl.example,
# never commit the real file):
#   terraform init -backend-config=backend.hcl
terraform {
  backend "s3" {}
}
