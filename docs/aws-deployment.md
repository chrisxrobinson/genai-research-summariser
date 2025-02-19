# AWS Deployment Architecture

## Components

1. **Storage**
   - S3 bucket for PDFs and summaries
   - DynamoDB for metadata storage

2. **Processing**
   - Lambda function triggered by S3 uploads
   - Weekly CloudWatch Event for report gathering

3. **API**
   - FastAPI backend deployed on Lambda
   - API Gateway for HTTP interface

## Setup Steps

1. Deploy infrastructure using Terraform
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

2. Configure environment variables:
   ```bash
   DYNAMODB_TABLE=research-metadata
   STORAGE_BUCKET=genai-research-storage
   ```

3. Deploy processing Lambda:
   ```bash
   cd backend
   zip -r process_reports.zip app/process_reports.py
   aws lambda update-function-code --function-name process-research-reports --zip-file fileb://process_reports.zip
   ```

## Architecture Benefits

- Serverless and scalable
- Cost-effective for varying loads
- Separate storage for metadata and full content
- Event-driven processing
