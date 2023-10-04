locals {
  dev_account_number = var.dev_account_number
  account_number = var.prod_account_number
  assets_bucket_name = var.assets_bucket_name
}

module "account_base" {
  source = "../../../terraform_modules/account_base"
  user_name = var.aws_account_user_name
  budget_alert_email = var.alarms_email
}

module "storage" {
  source = "../../../terraform_modules/storage"
  timestream_magnetic_retention_days = 1825
  timestream_memory_retention_hours = 6
  enable_delete_protection = true
  s3_bucket_name = local.assets_bucket_name
}

module "lambdas" {
  source = "../../../terraform_modules/lambdas"
  env_name = "prod"
  account_number = local.account_number
  auth_tokens_table_arn = module.storage.auth_tokens_table_arn
  metrics_table_arn = module.storage.metrics_table_arn
  egg_detector_cache_table_arn = module.storage.egg_detector_cache_table_arn
  image_uri = "${local.dev_account_number}.dkr.ecr.us-west-2.amazonaws.com/home_monitoring:latest"
  enable_functions = true
  alarms_email = var.alarms_email
  s3_bucket_name = local.assets_bucket_name
}

module "grafana" {
  source = "../../../terraform_modules/grafana"
  s3_assets_bucket_name = local.assets_bucket_name
  image_uri = "${local.dev_account_number}.dkr.ecr.us-west-2.amazonaws.com/home_monitoring:latest"
  env_name = "prod"
  vpc_main_id = module.account_base.vpc_id
  public_subnet_id = module.account_base.public_subnet_id
}
