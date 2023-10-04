output "metrics_table_arn" {
  value = aws_timestreamwrite_table.metrics.arn
}

output "auth_tokens_table_arn" {
  value = aws_dynamodb_table.home_monitoring_auth_tokens.arn
}

output "egg_detector_cache_table_arn" {
  value = aws_dynamodb_table.egg_detector_cache.arn
}

output "home_monitoring_bucket_name" {
  value = aws_s3_bucket.home_monitoring.arn
}
