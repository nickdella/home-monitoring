# this repository is shared with the prod environment
resource "aws_ecr_repository" "home_monitoring_repo" {
  name = "home_monitoring"
}

data "aws_iam_policy_document" "home_monitoring_repo" {
  statement {
    sid    = "cross_account_function"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [
        "arn:aws:iam::${local.prod_account_number}:user/terraform",
        "arn:aws:iam::${local.prod_account_number}:root"
      ]
    }

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
  }

  statement {
    sid    = "lambda_ecr_image_cross_account_retrieval_policy"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
  }

  statement {
    sid    = "lambda_ecr_image_cross_account_retrieval_policy_prod"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      values   = ["arn:aws:lambda:us-west-2:${local.prod_account_number}:function:*"]
      variable = "aws:sourceArn"
    }

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
  }
}

resource "aws_ecr_repository_policy" "home_monitoring_repo" {
  repository = aws_ecr_repository.home_monitoring_repo.name
  policy     = data.aws_iam_policy_document.home_monitoring_repo.json
}
