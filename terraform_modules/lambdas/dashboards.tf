resource "aws_cloudwatch_dashboard" "lambda" {
  dashboard_name = "Lambda"

  dashboard_body = jsonencode(
{
    "widgets": [
        {
            "height": 9,
            "width": 12,
            "y": 0,
            "x": 0,
            "type": "metric",
            "properties": {
                "metrics": [
                    [ "AWS/Lambda", "Invocations", "FunctionName", "home_monitoring_auth", "Resource", "home_monitoring_auth" ],
                    [ "...", "home_monitoring_scraper_flume", ".", "home_monitoring_scraper_flume" ],
                    [ "...", "home_monitoring_scraper_enphase", ".", "home_monitoring_scraper_enphase" ],
                    [ "...", "home_monitoring_scraper_yolink", ".", "home_monitoring_scraper_yolink" ],
                    [ "...", "home_monitoring_scraper_ecowitt", ".", "home_monitoring_scraper_ecowitt" ]
                ],
                "period": 300,
                "region": "us-west-2",
                "setPeriodToTimeRange": true,
                "sparkline": false,
                "stacked": true,
                "stat": "Average",
                "title": "Invocations",
                "trend": false,
                "view": "timeSeries"
            }
        },
        {
            "height": 9,
            "width": 11,
            "y": 0,
            "x": 12,
            "type": "metric",
            "properties": {
                "metrics": [
                    [ "AWS/Lambda", "Errors", "FunctionName", "home_monitoring_auth", "Resource", "home_monitoring_auth" ],
                    [ "...", "home_monitoring_scraper_ecowitt", ".", "home_monitoring_scraper_ecowitt" ],
                    [ "...", "home_monitoring_scraper_yolink", ".", "home_monitoring_scraper_yolink" ],
                    [ "...", "home_monitoring_scraper_flume", ".", "home_monitoring_scraper_flume" ],
                    [ "...", "home_monitoring_scraper_enphase", ".", "home_monitoring_scraper_enphase" ]
                ],
                "period": 300,
                "region": "us-west-2",
                "stacked": true,
                "stat": "Average",
                "title": "Errors",
                "view": "timeSeries"
            }
        }
    ]
}
  )
}