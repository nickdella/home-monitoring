# Create a new HTTP API
resource "aws_apigatewayv2_api" "grafana_launcher" {
  name = "grafana_launcher"
  protocol_type = "HTTP"
}

# Set up an integration between our HTTP API and the redirect Lambda
resource "aws_apigatewayv2_integration" "grafana_launcher_api_integration" {
  api_id = aws_apigatewayv2_api.grafana_launcher.id
  integration_type = "AWS_PROXY"

  connection_type = "INTERNET"
  description = "Route to grafana_launcher lambda"
  integration_method = "POST"
  integration_uri = aws_lambda_function.grafana_launcher.invoke_arn
  timeout_milliseconds = 30 * 1000
}

# Set up a route in API Gateway to expect traffic on, and redirect said
# traffic to the redirect Lambda
resource "aws_apigatewayv2_route" "grafana_launcher_route" {
  api_id = aws_apigatewayv2_api.grafana_launcher.id
  route_key = "GET /grafana"
  target = "integrations/${aws_apigatewayv2_integration.grafana_launcher_api_integration.id}"
}

resource "aws_apigatewayv2_stage" "grafana_launcher_stage" {
  api_id = aws_apigatewayv2_api.grafana_launcher.id
  name = "default"
  auto_deploy = true  # Changes to API will be auto-deployed to default stage

  default_route_settings {
    throttling_burst_limit = 2
    throttling_rate_limit = 2
  }
}

output "invoke_url" {
  value = "Grafana launcher URL: ${aws_apigatewayv2_stage.grafana_launcher_stage.invoke_url}/grafana"
}