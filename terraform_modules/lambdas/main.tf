resource "aws_lambda_function" "home_monitoring_scraper" {
  for_each = var.scraper_configs
  function_name = "home_monitoring_scraper_${each.key}"
  role          = aws_iam_role.home_monitoring_function_role.arn
  memory_size   = 128 # MB
  timeout       = 10 # seconds

  package_type  = "Image"
  image_uri     = var.image_uri

  environment {
    variables = {
      ENVIRONMENT = var.env_name
    }
  }
}

resource "aws_cloudwatch_log_group" "home_monitoring_scraper_log_group" {
  for_each = aws_lambda_function.home_monitoring_scraper
  name              = "/aws/lambda/${aws_lambda_function.home_monitoring_scraper[each.key].function_name}"
  retention_in_days = 14
}


resource "aws_cloudwatch_event_rule" "home_monitoring_lambda_event_rule" {
  for_each = var.scraper_configs
  name = "home_monitoring_lambda_event_rule_${each.key}"
  description = "Event trigger for ${each.key}, running on schedule ${each.value}"
  schedule_expression = each.value
  # we manually enable this via the console for dev testing
  is_enabled = var.enable_functions
}

resource "aws_cloudwatch_event_target" "home_monitoring_lambda_target" {
  for_each = var.scraper_configs
  rule = "home_monitoring_lambda_event_rule_${each.key}"
  arn = "arn:aws:lambda:us-west-2:${var.account_number}:function:home_monitoring_scraper_${each.key}"
  retry_policy {
    maximum_event_age_in_seconds = 3 * 60 * 60 # 3 hours
    maximum_retry_attempts = 3
  }
  input = <<JSON
  {
    "scraper_class": "home_monitoring.scrapers.${each.key}.${title(each.key)}Scraper"
  }
  JSON
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  for_each = var.scraper_configs
  action = "lambda:InvokeFunction"
  function_name = "home_monitoring_scraper_${each.key}"
  principal = "events.amazonaws.com"
  # TODO extract account ID into constant
  source_arn = "arn:aws:events:us-west-2:${var.account_number}:rule/home_monitoring_lambda_event_rule_${each.key}"
}

# auth_token_refresher lambda function and trigger
resource "aws_lambda_function" "home_monitoring_auth" {
  function_name = "home_monitoring_auth"
  role          = aws_iam_role.home_monitoring_function_role.arn
  memory_size   = 128 # MB
  timeout       = 30 # seconds

  package_type  = "Image"
  image_uri      = var.image_uri
  image_config {
    command = ["home_monitoring.lambdas.auth_token_refresher.lambda_handler"]
  }

  environment {
    variables = {
      ENVIRONMENT = var.env_name
    }
  }
}

resource "aws_cloudwatch_log_group" "home_monitoring_auth_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.home_monitoring_auth.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_event_rule" "home_monitoring_auth_lambda_event_rule" {
  name = "home_monitoring_auth_lambda_event_rule"
  description = "Event trigger for auth token refresh"
  schedule_expression = "cron(0 4 * * ? *)"
  # we manually enable this via the console for dev testing
  is_enabled = var.enable_functions
}

resource "aws_cloudwatch_event_target" "home_monitoring_auth_lambda_target" {
  rule = aws_cloudwatch_event_rule.home_monitoring_auth_lambda_event_rule.name
  arn = aws_lambda_function.home_monitoring_auth.arn
  retry_policy {
    maximum_event_age_in_seconds = 3 * 60 * 60 # 3 hours
    maximum_retry_attempts = 3
  }
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_auth_lambda" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.home_monitoring_auth.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.home_monitoring_auth_lambda_event_rule.arn
}

# home_monitoring_egg_detector lambda function
resource "aws_lambda_function" "home_monitoring_egg_detector" {
  function_name = "home_monitoring_egg_detector"
  role          = aws_iam_role.home_monitoring_function_role.arn
  memory_size   = 128 # MB
  timeout       = 30 # seconds

  package_type  = "Image"
  image_uri      = var.image_uri
  image_config {
    command = ["home_monitoring.lambdas.egg_detector.lambda_handler"]
  }

  environment {
    variables = {
      ENVIRONMENT = var.env_name
    }
  }
}

# Allow AWS API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "home_monitoring_egg_detector_lambda_permission" {
  statement_id = "home_monitoring_egg_detector_lambda_permission"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.home_monitoring_egg_detector.function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.egg_detector.execution_arn}/*"
}

resource "aws_cloudwatch_log_group" "home_monitoring_egg_detector" {
  name              = "/aws/lambda/${aws_lambda_function.home_monitoring_egg_detector.function_name}"
  retention_in_days = 14
}
