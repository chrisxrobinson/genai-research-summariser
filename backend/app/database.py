import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from .config import get_settings

settings = get_settings()


class Storage:
    def __init__(self):
        # Configure AWS clients with environment variables
        self._setup_clients()

    def _setup_clients(self):
        """Initialize AWS clients with appropriate endpoints"""
        session_kwargs = {
            "region_name": settings.aws_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }

        if settings.dev_mode:
            self.dynamodb = boto3.resource(
                "dynamodb",
                endpoint_url=settings.dynamodb_endpoint,
                **session_kwargs
            )
            self.s3 = boto3.client(
                "s3", 
                endpoint_url=settings.s3_endpoint,
                **session_kwargs
            )
        else:
            self.dynamodb = boto3.resource("dynamodb", **session_kwargs)
            self.s3 = boto3.client("s3", **session_kwargs)

        self.table = self.dynamodb.Table(settings.dynamodb_table)
        self.bucket_name = settings.s3_bucket_name

    async def get_document_metadata(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document metadata from DynamoDB"""
        try:
            response = self.table.get_item(Key={"id": str(document_id)})
            return response.get("Item")
        except ClientError as e:
            print(f"Error getting document metadata: {e}")
            return None

    async def save_document_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Save document metadata to DynamoDB"""
        try:
            # Convert any UUID to string
            if "id" in metadata and isinstance(metadata["id"], UUID):
                metadata["id"] = str(metadata["id"])
                
            # Convert datetime objects to ISO format strings
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    metadata[key] = value.isoformat()
                
            self.table.put_item(Item=metadata)
            return True
        except ClientError as e:
            print(f"Error saving document metadata: {e}")
            return False

    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in DynamoDB"""
        try:
            response = self.table.scan()
            return response.get("Items", [])
        except ClientError as e:
            print(f"Error listing documents: {e}")
            return []

    async def upload_pdf(self, document_id: UUID, file_content: bytes) -> Optional[str]:
        """Upload PDF to S3 and return the key"""
        try:
            key = f"pdfs/{document_id}.pdf"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType="application/pdf"
            )
            return key
        except ClientError as e:
            print(f"Error uploading PDF: {e}")
            return None

    async def upload_text(self, document_id: UUID, text: str, text_type: str) -> Optional[str]:
        """Upload text content to S3 and return the key"""
        try:
            key = f"{text_type}/{document_id}.txt"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=text,
                ContentType="text/plain"
            )
            return key
        except ClientError as e:
            print(f"Error uploading text: {e}")
            return None

    async def get_pdf(self, key: str) -> Optional[bytes]:
        """Get PDF content from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            print(f"Error getting PDF: {e}")
            return None

    async def get_text(self, key: str) -> Optional[str]:
        """Get text content from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            print(f"Error getting text: {e}")
            return None

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete document and all associated files"""
        try:
            # Get document metadata
            metadata = await self.get_document_metadata(document_id)
            if not metadata:
                return False
                
            # Delete from DynamoDB
            self.table.delete_item(Key={"id": str(document_id)})
            
            # Delete all S3 objects with prefix
            prefix = f"{document_id}"
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            object_list = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        object_list.append({"Key": obj["Key"]})
            
            if object_list:
                self.s3.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={"Objects": object_list}
                )
                
            return True
        except ClientError as e:
            print(f"Error deleting document: {e}")
            return False


# Initialize storage singleton
storage = Storage()
