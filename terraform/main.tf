provider "aws" {
  region = var.aws_region
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_role" {
  name = "genai_research_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda Functions
resource "aws_iam_policy" "lambda_policy" {
  name        = "genai_research_lambda_policy"
  description = "Policy for GenAI Research Summariser Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.research_storage.arn}",
          "${aws_s3_bucket.research_storage.arn}/*"
        ]
      },
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.research_metadata.arn
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

// S3 bucket for storing reports and summaries
resource "aws_s3_bucket" "research_storage" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_cors_configuration" "cors_config" {
  bucket = aws_s3_bucket.research_storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"] // Restrict in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

// DynamoDB table for research metadata
resource "aws_dynamodb_table" "research_metadata" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  stream_enabled = true

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "GenAI Research Metadata"
  }
}

// Lambda for processing new reports
resource "aws_lambda_function" "process_reports" {
  filename         = "process_reports.zip"
  function_name    = "process-research-reports"
  role            = aws_iam_role.lambda_role.arn
  handler         = "process_reports.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.research_metadata.name
      STORAGE_BUCKET = aws_s3_bucket.research_storage.id
    }
  }
}

# Lambda function for API backend
resource "aws_lambda_function" "api_lambda" {
  function_name = "genai-research-api"
  filename      = "../backend_lambda.zip" // You'll need to create this deployment package
  handler       = "app.main.handler"
  runtime       = "python3.9"
  timeout       = 30
  memory_size   = 512
  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.research_metadata.name
      S3_BUCKET_NAME = aws_s3_bucket.research_storage.id
      AWS_REGION = var.aws_region
      PINECONE_API_KEY = var.pinecone_api_key
      PINECONE_ENVIRONMENT = var.pinecone_environment
      PINECONE_INDEX_NAME = var.pinecone_index_name
      EMBEDDING_DIMENSION = var.embedding_dimension
      MISTRAL_API_KEY = var.mistral_api_key
    }
  }
}

resource "aws_apigatewayv2_api" "api_gateway" {
  name          = "genai-research-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"] // Restrict in production
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

// API Gateway integration with Lambda
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.api_gateway.id
  integration_type = "AWS_PROXY"
  
  integration_uri           = aws_lambda_function.api_lambda.invoke_arn
  integration_method        = "POST"
  payload_format_version    = "2.0"
}

// API Gateway route for all paths
resource "aws_apigatewayv2_route" "api_route" {
  api_id    = aws_apigatewayv2_api.api_gateway.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

// API Gateway stage
resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api_gateway.id
  name        = "prod"
  auto_deploy = true
}

// Lambda permission to allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_lambda.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api_gateway.execution_arn}/*/*"
}

// CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_lambda.function_name}"
  retention_in_days = 14
}

// Output the API Gateway URL
output "api_gateway_url" {
  value = "${aws_apigatewayv2_stage.api_stage.invoke_url}"
}
