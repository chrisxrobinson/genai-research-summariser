provider "aws" {
  region = "us-east-1"
}

resource "aws_lambda_function" "backend_lambda" {
  function_name = "genaiResearchSummariser"
  filename      = "path/to/backend.zip" # Adjust packaging accordingly
  handler       = "app.main.handler"
  runtime       = "python3.9"
  role          = "arn:aws:iam::123456789012:role/lambda_basic_execution"
}

resource "aws_apigatewayv2_api" "api_gateway" {
  name          = "genaiResearchAPI"
  protocol_type = "HTTP"
}

# ...additional configuration...
