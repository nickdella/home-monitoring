resource "aws_timestreamwrite_database" "home_monitoring" {
  database_name = "home_monitoring"
  lifecycle {
    # can't use env-specific variable here. See https://github.com/hashicorp/terraform/issues/22544
    prevent_destroy = true
  }
}

resource "aws_timestreamwrite_table" "metrics" {
  database_name = aws_timestreamwrite_database.home_monitoring.database_name
  table_name    = "metrics"

  retention_properties {
    magnetic_store_retention_period_in_days = var.timestream_magnetic_retention_days
    memory_store_retention_period_in_hours  = var.timestream_memory_retention_hours
  }

  magnetic_store_write_properties {
    enable_magnetic_store_writes = true
  }

  schema {
    composite_partition_key {
      type                  = "MEASURE"
    }
  }

  lifecycle {
    # can't use env-specific variable here. See https://github.com/hashicorp/terraform/issues/22544
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "home_monitoring_auth_tokens" {
  name           = "home_monitoring_auth_tokens"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "app_name"

  attribute {
    name = "app_name"
    type = "S"
  }

  deletion_protection_enabled = var.enable_delete_protection

  lifecycle {
    # can't use env-specific variable here. See https://github.com/hashicorp/terraform/issues/22544
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "egg_detector_cache" {
  name           = "egg_detector_cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "nesting_box"

  attribute {
    name = "nesting_box"
    type = "S"
  }

  deletion_protection_enabled = var.enable_delete_protection

  lifecycle {
    # can't use env-specific variable here. See https://github.com/hashicorp/terraform/issues/22544
    prevent_destroy = true
  }
}
