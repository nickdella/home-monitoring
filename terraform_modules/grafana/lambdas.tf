data "aws_iam_policy_document" "AWSLambdaTrustPolicy" {
  statement {
    actions    = ["sts:AssumeRole"]
    effect     = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "grafana_launcher_policy_document" {
  statement {
    effect  = "Allow"
    actions = [
      "ec2:Describe*",
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect  = "Allow"
    actions = [
      "autoscaling:Describe*",
      "autoscaling:SetDesiredCapacity"
    ]
    resources = [
      "*",
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role" "grafana_launcher_role" {
  name               = "grafana_launcher_role"
  assume_role_policy = data.aws_iam_policy_document.AWSLambdaTrustPolicy.json
}

resource "aws_iam_policy" "grafana_launcher_policy" {
  name        = "grafana_launcher_policy"
  policy      = data.aws_iam_policy_document.grafana_launcher_policy_document.json
}

resource "aws_iam_role_policy_attachment" "grafana_launcher_policy_attachment" {
  role       = aws_iam_role.grafana_launcher_role.name
  policy_arn = aws_iam_policy.grafana_launcher_policy.arn
}

# Grafana launcher function driven by API Gateway requests
resource "aws_lambda_function" "grafana_launcher" {
  function_name = "home_monitoring_grafana_launcher"
  role          = aws_iam_role.grafana_launcher_role.arn
  memory_size   = 128 # MB
  timeout       = 300 # seconds

  package_type  = "Image"
  image_uri      = var.image_uri
  image_config {
    command = ["home_monitoring.lambdas.grafana_launcher.lambda_handler"]
  }

  environment {
    variables = {
      ASG_NAME = aws_autoscaling_group.grafana_asg.name
      ENVIRONMENT = var.env_name
    }
  }
}

resource "aws_cloudwatch_log_group" "grafana_launcher_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.grafana_launcher.function_name}"
  retention_in_days = 14
}

# Allow AWS API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "grafana_launcher_lambda_permission" {
  statement_id = "grafana_launcher_lambda_permission"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.grafana_launcher.function_name
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_apigatewayv2_api.grafana_launcher.execution_arn}/*"
}

# Grafana auto-shutdown function driven by scheduled CloudWatch Events
resource "aws_lambda_function" "grafana_auto_shutdown" {
  function_name = "home_monitoring_grafana_auto_shutdown"
  role          = aws_iam_role.grafana_launcher_role.arn
  memory_size   = 128 # MB
  timeout       = 300 # seconds

  package_type  = "Image"
  image_uri      = var.image_uri
  image_config {
    command = ["home_monitoring.lambdas.grafana_auto_shutdown.lambda_handler"]
  }

  environment {
    variables = {
      ASG_NAME = aws_autoscaling_group.grafana_asg.name
    }
  }
}

resource "aws_cloudwatch_log_group" "grafana_auto_shutdown_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.grafana_auto_shutdown.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_event_rule" "grafana_auto_shutdown_event_rule" {
  name = "grafana_auto_shutdown_event_rule"
  description = "Event trigger for grafana auto shutdown"
  schedule_expression = "cron(0,30 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "grafana_auto_shutdown_lambda_target" {
  rule = aws_cloudwatch_event_rule.grafana_auto_shutdown_event_rule.name
  arn = aws_lambda_function.grafana_auto_shutdown.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_grafana_auto_shutdown_lambda" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.grafana_auto_shutdown.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.grafana_auto_shutdown_event_rule.arn
}
