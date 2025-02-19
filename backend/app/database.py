import os

import boto3
from botocore.exceptions import ClientError


class Storage:
    def __init__(self, table_name=None, bucket_name=None):
        # Configure AWS clients with environment variables
        dynamodb_endpoint = os.getenv(
            "DYNAMODB_ENDPOINT", "http://localhost:8000"
        )
        aws_region = os.getenv("AWS_REGION", "us-east-1")

        self.dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=dynamodb_endpoint,
            region_name=aws_region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        self.s3 = boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        table_name = table_name or os.getenv(
            "DYNAMODB_TABLE", "research-metadata"
        )
        self.table = self.dynamodb.Table(table_name)
        self.bucket = bucket_name or os.getenv(
            "STORAGE_BUCKET", "research-storage"
        )

    async def get_item(self, id: str):
        try:
            response = self.table.get_item(Key={"id": str(id)})
            return response.get("Item")
        except ClientError as e:
            print(f"Error: {e}")
            return None

    async def put_item(self, item: dict):
        return self.table.put_item(Item=item)

    async def get_s3_object(self, key: str):
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            print(f"Error: {e}")
            return None


# Initialize storage with environment variables
storage = Storage()
