# Create a new HTTP API
resource "aws_apigatewayv2_api" "egg_detector" {
  name = "egg_detector"
  protocol_type = "HTTP"
}

# Set up an integration between our HTTP API and the redirect Lambda
resource "aws_apigatewayv2_integration" "egg_detector_api_integration" {
  api_id = aws_apigatewayv2_api.egg_detector.id
  integration_type = "AWS_PROXY"

  connection_type = "INTERNET"
  description = "Route to egg_detector lambda"
  integration_method = "POST"
  integration_uri = aws_lambda_function.home_monitoring_egg_detector.invoke_arn
  timeout_milliseconds = 30 * 1000
}

# Set up a route in API Gateway to expect traffic on, and redirect said
# traffic to the redirect Lambda
resource "aws_apigatewayv2_route" "egg_detector_route" {
  api_id = aws_apigatewayv2_api.egg_detector.id
  route_key = "GET /egg_detector"
  target = "integrations/${aws_apigatewayv2_integration.egg_detector_api_integration.id}"
}

resource "aws_apigatewayv2_stage" "egg_detector_stage" {
  api_id = aws_apigatewayv2_api.egg_detector.id
  name = "default"
  auto_deploy = true  # Changes to API will be auto-deployed to default stage

  default_route_settings {
    throttling_burst_limit = 2
    throttling_rate_limit = 2
  }
}

output "invoke_url" {
  value = "Egg Detector URL: ${aws_apigatewayv2_stage.egg_detector_stage.invoke_url}/egg_detector"
}