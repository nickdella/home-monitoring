locals {
  schedules = {
    "hourly": "cron(* 1 * * ? *)"
    "daily": "cron(30 23 * * ? *)"
  }
}

resource "aws_lambda_function" "home_monitoring_timestream" {
  function_name = "home_monitoring_timestream"
  role          = aws_iam_role.home_monitoring_function_role.arn
  memory_size   = 128 # MB
  timeout       = 60 # seconds

  package_type  = "Image"
  image_uri      = var.image_uri
  image_config {
    command = ["home_monitoring.lambdas.monitoring.lambda_handler"]
  }

  environment {
    variables = {
      ENVIRONMENT = var.env_name
      ALARM_TOPIC_ARN = aws_sns_topic.alarms.arn
    }
  }
}

resource "aws_cloudwatch_log_group" "home_monitoring_timestream_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.home_monitoring_timestream.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_event_rule" "home_monitoring_timestream_lambda_event_rule" {
  for_each = local.schedules
  name = "home_monitoring_timestream_lambda_event_rule_${each.key}"
  description = "Event trigger ${each.key} monitoring job"
  schedule_expression = each.value
  # we manually enable this via the console for dev testing
  is_enabled = var.enable_monitoring
}

resource "aws_cloudwatch_event_target" "home_monitoring_timestream_lambda_target" {
  for_each = local.schedules
  rule = "home_monitoring_timestream_lambda_event_rule_${each.key}"
  arn = aws_lambda_function.home_monitoring_timestream.arn
  retry_policy {
    maximum_event_age_in_seconds = 3 * 60 * 60 # 3 hours
    maximum_retry_attempts = 1
  }
  input = <<JSON
  {
    "schedule": "${each.key}"
  }
  JSON
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_timestream_lambda" {
  for_each = local.schedules
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.home_monitoring_timestream.function_name
  principal = "events.amazonaws.com"
  # TODO extract account ID into constant
  source_arn = "arn:aws:events:us-west-2:${var.account_number}:rule/home_monitoring_timestream_lambda_event_rule_${each.key}"
}

