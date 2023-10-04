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

resource "aws_iam_role" "home_monitoring_function_role" {
  name               = "home_monitoring_function_role"
  assume_role_policy = data.aws_iam_policy_document.AWSLambdaTrustPolicy.json
}

data "aws_iam_policy_document" "home_monitoring_function_policy_document" {
  statement {
    effect    = "Allow"
    actions   = [
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:ConditionCheckItem",
      "dynamodb:DescribeTable",
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:PutItem",
      "dynamodb:Scan",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.auth_tokens_table_arn,
      var.egg_detector_cache_table_arn
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "timestream:CancelQuery",
      "timestream:DescribeTable",
      "timestream:ListMeasures",
      "timestream:Select",
      "timestream:SelectValues",
      "timestream:WriteRecords",
    ]
    resources = [
      var.metrics_table_arn
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "timestream:DescribeEndpoints",
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "sns:publish",
    ]
    resources = [
      aws_sns_topic.alarms.arn
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_bucket_name}"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "s3:GetObject*",
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_bucket_name}/*"
    ]
  }
}

resource "aws_iam_policy" "home_monitoring_function_policy" {
  name        = "home_monitoring_function_policy"
  policy      = data.aws_iam_policy_document.home_monitoring_function_policy_document.json
}

resource "aws_iam_role_policy_attachment" "home_monitoring_lambda_policy" {
  role       = aws_iam_role.home_monitoring_function_role.name
  policy_arn = aws_iam_policy.home_monitoring_function_policy.arn
}
