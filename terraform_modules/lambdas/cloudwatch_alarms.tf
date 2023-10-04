resource "aws_sns_topic" "alarms" {
  name = "alarms_topic"
}

resource "aws_sns_topic_subscription" "alarms" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarms_email
}

resource "aws_cloudwatch_metric_alarm" "lambda_functions_success_rate_low" {
  alarm_name          = "lambda_functions_success_rate_low_${var.env_name}"
  alarm_description   = "Lambda function success rate in ${var.env_name} has fallen below 100% over the past hour"

  comparison_operator = "LessThanThreshold"
  threshold           = 100
  evaluation_periods  = 4
  datapoints_to_alarm = 2
  alarm_actions       = [aws_sns_topic.alarms.arn]

  metric_query {
    id          = "rate"
    expression  = "100 - 100 * errors / MAX([errors, invocations])"
    label       = "Success Rate"
    return_data = "true"
  }

  metric_query {
    id = "errors"

    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 3600
      stat        = "Sum"
      unit        = "Count"
    }
  }

  metric_query {
    id = "invocations"

    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 3600
      stat        = "Sum"
      unit        = "Count"
    }
  }
}

