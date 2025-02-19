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

// S3 bucket for storing reports and summaries
resource "aws_s3_bucket" "research_storage" {
  bucket = "genai-research-storage"
}

// DynamoDB table for research metadata
resource "aws_dynamodb_table" "research_metadata" {
  name           = "research-metadata"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  stream_enabled = true

  attribute {
    name = "id"
    type = "S"
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

resource "aws_apigatewayv2_api" "api_gateway" {
  name          = "genaiResearchAPI"
  protocol_type = "HTTP"
}

# ...additional configuration...
