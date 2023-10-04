resource "aws_budgets_budget" "daily_budget" {
  name              = "daily-budget"
  budget_type       = "COST"
  limit_amount      = "2.0"
  limit_unit        = "USD"
  time_period_start = "2023-08-01_00:00"
  time_period_end   = "2085-01-01_00:00"
  time_unit         = "DAILY"
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}

resource "aws_budgets_budget" "monthly_budget" {
  name              = "monthly-budget"
  budget_type       = "COST"
  limit_amount      = "10.0"
  limit_unit        = "USD"
  time_period_start = "2023-08-01_00:00"
  time_period_end   = "2085-01-01_00:00"
  time_unit         = "MONTHLY"
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}
