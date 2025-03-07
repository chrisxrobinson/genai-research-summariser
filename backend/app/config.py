import os
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Environment mode
    dev_mode: bool = os.environ.get("DEV_MODE", "False").lower() == "true"
    
    # AWS Configuration
    aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
    aws_access_key_id: str = os.environ.get("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    
    # DynamoDB Configuration
    dynamodb_table: str = os.environ.get("DYNAMODB_TABLE", "research-metadata")
    dynamodb_endpoint: str = os.environ.get("DYNAMODB_ENDPOINT", None)  # For local development
    
    # S3 Configuration
    s3_bucket_name: str = os.environ.get("S3_BUCKET_NAME", "genai-research-storage")
    s3_endpoint: str = os.environ.get("S3_ENDPOINT", None)  # For local development
    
    # Vector Database Configuration
    vector_db: Literal["pinecone", "qdrant"] = os.environ.get("VECTOR_DB", "pinecone")
    
    # Pinecone Configuration (for production)
    pinecone_api_key: str = os.environ.get("PINECONE_API_KEY", "")
    pinecone_environment: str = os.environ.get("PINECONE_ENVIRONMENT", "us-west1-gcp")
    pinecone_index_name: str = os.environ.get("PINECONE_INDEX_NAME", "research-embeddings")
    
    # Qdrant Configuration (for local development)
    qdrant_url: str = os.environ.get("QDRANT_URL", "http://localhost:6333")
    qdrant_collection_name: str = os.environ.get("QDRANT_COLLECTION", "research-embeddings")
    
    # Embedding Configuration
    embedding_dimension: int = int(os.environ.get("EMBEDDING_DIMENSION", "1536"))
    
    # Mistral API
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")

    # OpenAI API
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        case_sensitive = False


@lru_cache()
def get_settings():
    """Returns cached settings to avoid reloading from environment each time"""
    return Settings()
