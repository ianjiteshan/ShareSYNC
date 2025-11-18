# backend/src/services/minio_client.py
import os
import logging
import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class MinIOClient:
    def __init__(self, endpoint_url=None, access_key=None, secret_key=None, bucket_name=None, region=None):
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT")
        self.access_key = access_key or os.getenv("S3_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("S3_SECRET_KEY")
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET")
        self.region = region or os.getenv("S3_REGION", "us-east-1")

        # Use signature v4 for compatibility
        cfg = Config(signature_version='s3v4', region_name=self.region)
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=cfg
        )

    def ensure_bucket(self):
        # Try to create bucket if not existing (idempotent)
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except ClientError as e:
                logger.warning("Could not create bucket: %s", e)

    def upload_file(self, object_key, file_bytes, content_type="application/octet-stream"):
        """
        Upload bytes and return dict { success, object_key, download_url (presigned) }
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type
            )
            # Return a presigned GET URL (short-lived)
            presigned = self.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=3600
            )
            return {
                "success": True,
                "object_key": object_key,
                "download_url": presigned,
                "content_type": content_type
            }
        except (BotoCoreError, ClientError) as e:
            logger.exception("upload_file failed: %s", e)
            return {"success": False, "error": str(e)}

    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn=3600):
        try:
            return self.s3_client.generate_presigned_url(ClientMethod, Params=Params, ExpiresIn=ExpiresIn)
        except Exception as e:
            logger.exception("generate_presigned_url failed: %s", e)
            raise

    def delete_file(self, object_key):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return {"success": True}
        except Exception as e:
            logger.exception("delete_file failed: %s", e)
            return {"success": False, "error": str(e)}

# singleton
minio_client = MinIOClient()
