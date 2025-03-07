#!/usr/bin/env bash
set -e

echo "Initializing LocalStack resources..."

# Function to retry commands with backoff
retry() {
    local max_attempts=5
    local attempt=1
    local backoff=1

    until "$@"; do
        if (( attempt >= max_attempts )); then
            echo "Command failed after $attempt attempts: $*" >&2
            return 1
        fi
        
        echo "Command failed, retrying in ${backoff}s (attempt $attempt/$max_attempts): $*" >&2
        sleep $backoff
        
        attempt=$((attempt + 1))
        backoff=$((backoff * 2))
    done
    return 0
}

# Check if S3 is available
echo "Checking S3 service availability..."
retry awslocal s3 ls >/dev/null 2>&1

# Create the S3 bucket if it doesn't exist
if ! awslocal s3 ls "s3://genai-research-storage" >/dev/null 2>&1; then
    echo "Creating S3 bucket: genai-research-storage"
    awslocal s3 mb s3://genai-research-storage
    
    # Set bucket policy to public-read (for development only)
    echo "Setting bucket ACL to public-read"
    awslocal s3api put-bucket-acl --bucket genai-research-storage --acl public-read
else
    echo "S3 bucket genai-research-storage already exists"
fi

# Check if DynamoDB table exists
echo "Checking if DynamoDB table exists..."
if ! awslocal dynamodb describe-table --table-name research-metadata >/dev/null 2>&1; then
    echo "Creating DynamoDB table: research-metadata"
    # Create DynamoDB table
    awslocal dynamodb create-table \
      --table-name research-metadata \
      --attribute-definitions AttributeName=id,AttributeType=S \
      --key-schema AttributeName=id,KeyType=HASH \
      --billing-mode PAY_PER_REQUEST
else
    echo "DynamoDB table research-metadata already exists"
fi

echo "LocalStack initialization complete!"
