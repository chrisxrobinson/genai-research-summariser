variable "aws_region" {
  description = "AWS region to deploy to"
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for research storage"
  default     = "genai-research-storage"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for research metadata"
  default     = "research-metadata"
}

variable "pinecone_api_key" {
  description = "API key for Pinecone vector database"
  sensitive   = true
}

variable "pinecone_environment" {
  description = "Pinecone environment"
  default     = "us-west1-gcp"
}

variable "pinecone_index_name" {
  description = "Name of the Pinecone index"
  default     = "research-embeddings"
}

variable "embedding_dimension" {
  description = "Dimension of embeddings"
  default     = 1536
}

variable "mistral_api_key" {
  description = "API key for Mistral AI"
  sensitive   = true
}
