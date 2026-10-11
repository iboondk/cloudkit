provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "cloudkit"
      Env       = "dev"
      ManagedBy = "terraform"
    }
  }
}

module "network" {
  source = "../../modules/network"

  name = var.name
}

module "db" {
  source = "../../modules/db"

  name                 = var.name
  private_subnet_ids   = module.network.private_subnet_ids
  db_security_group_id = module.network.db_security_group_id
}

module "compute" {
  source = "../../modules/compute"

  name                  = var.name
  aws_region            = var.aws_region
  vpc_id                = module.network.vpc_id
  public_subnet_ids     = module.network.public_subnet_ids
  alb_security_group_id = module.network.alb_security_group_id
  app_security_group_id = module.network.app_security_group_id
  container_image       = var.container_image
  db_address            = module.db.address
  db_port               = module.db.port
  db_name               = module.db.db_name
  db_secret_arn         = module.db.master_user_secret_arn
}

module "edge" {
  source = "../../modules/edge"

  name         = var.name
  alb_dns_name = module.compute.alb_dns_name
}

module "observability" {
  source = "../../modules/observability"

  name                    = var.name
  aws_region              = var.aws_region
  alb_arn_suffix          = module.compute.alb_arn_suffix
  target_group_arn_suffix = module.compute.target_group_arn_suffix
  ecs_cluster_name        = module.compute.cluster_name
  ecs_service_name        = module.compute.service_name
  db_instance_id          = module.db.instance_id
  alarm_email             = var.alarm_email
}
