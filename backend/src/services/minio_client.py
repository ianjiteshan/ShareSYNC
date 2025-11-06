import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
import uuid
from datetime import datetime, timedelta
import hashlib
import mimetypes

class MinIOClient:
    def __init__(self):
        # MinIO configuration
        self.endpoint_url = os.getenv('MINIO_ENDPOINT', 'http://localhost:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket_name = os.getenv('MINIO_BUCKET', 'sharesync-files')
        self.region = os.getenv('MINIO_REGION', 'us-east-1')
        
        # Initialize S3 client with MinIO configuration
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(signature_version='s3v4')
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                try:
                    if self.region != 'us-east-1':
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"Created bucket '{self.bucket_name}'")
                    
                    # Set bucket policy for public read access to shared files
                    self._set_bucket_policy()
                except ClientError as create_error:
                    print(f"Failed to create bucket: {create_error}")
                    raise
            else:
                print(f"Error checking bucket: {e}")
                raise
        except NoCredentialsError:
            print("MinIO credentials not found. Please check your configuration.")
            raise
        except Exception as e:
            print(f"Unexpected error with MinIO connection: {e}")
            raise
    
    def _set_bucket_policy(self):
        """Set bucket policy to allow public read access to shared files"""
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/shared/*"
                }
            ]
        }
        
        try:
            import json
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("Set bucket policy for public access to shared files")
        except ClientError as e:
            print(f"Warning: Could not set bucket policy: {e}")
    
    def upload_file(self, file_obj, filename, user_id, expiry_hours=24, password=None):
        """
        Upload a file to MinIO storage
        
        Args:
            file_obj: File object to upload
            filename: Original filename
            user_id: ID of the user uploading the file
            expiry_hours: Hours until the file expires (default 24)
            password: Optional password protection
            
        Returns:
            dict: Upload result with file info and URLs
        """
        try:
            # Generate unique file ID and key
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(filename)[1]
            safe_filename = f"{file_id}{file_extension}"
            
            # Determine if file should be publicly accessible
            is_public = password is None
            key_prefix = "shared" if is_public else "private"
            object_key = f"{key_prefix}/{user_id}/{safe_filename}"
            
            # Get file content and metadata
            file_obj.seek(0)
            file_content = file_obj.read()
            file_size = len(file_content)
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Calculate expiry time
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Prepare metadata
            metadata = {
                'original-filename': filename,
                'file-id': file_id,
                'user-id': user_id,
                'upload-time': datetime.utcnow().isoformat(),
                'expiry-time': expiry_time.isoformat(),
                'file-hash': file_hash,
                'file-size': str(file_size),
                'has-password': str(password is not None).lower()
            }
            
            # Add password hash to metadata if provided
            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                metadata['password-hash'] = password_hash
            
            # Upload file to MinIO
            file_obj.seek(0)
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': metadata
                }
            )
            
            # Generate URLs
            if is_public:
                # Public URL for direct access
                public_url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            else:
                public_url = None
            
            # Generate a short-lived presigned URL for immediate return (not for download)
            # The actual download link will be generated by the download route
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=60 # 1 minute
            )
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'size': file_size,
                'content_type': content_type,
                'hash': file_hash,
                'object_key': object_key,
                'public_url': public_url,
                'download_url': download_url,
                'expiry_time': expiry_time.isoformat(),
                'has_password': password is not None,
                'upload_time': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            print(f"MinIO upload error: {e}")
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
        except Exception as e:
            print(f"Unexpected upload error: {e}")
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
    
    def get_file_info(self, object_key):
        """Get file information and metadata"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            
            metadata = response.get('Metadata', {})
            
            return {
                'success': True,
                'file_id': metadata.get('file-id'),
                'filename': metadata.get('original-filename'),
                'size': int(metadata.get('file-size', 0)),
                'content_type': response.get('ContentType'),
                'hash': metadata.get('file-hash'),
                'user_id': metadata.get('user-id'),
                'upload_time': metadata.get('upload-time'),
                'expiry_time': metadata.get('expiry-time'),
                'has_password': metadata.get('has-password', 'false').lower() == 'true',
                'password_hash': metadata.get('password-hash'),
                'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'success': False, 'error': 'File not found'}
            return {'success': False, 'error': f'Failed to get file info: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def delete_file(self, object_key):
        """Delete a file from MinIO storage"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            
            return {'success': True, 'message': 'File deleted successfully'}
            
        except ClientError as e:
            return {'success': False, 'error': f'Delete failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def generate_presigned_url(self, object_key, expiration=3600):
        """Generate a presigned URL for a given object key."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL for {object_key}: {e}")
            return None

# Global MinIO client instance
minio_client = MinIOClient()
