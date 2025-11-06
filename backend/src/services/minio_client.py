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
            
            # Generate presigned URL for download (valid for 7 days or until expiry)
            presigned_expiry = min(expiry_hours * 3600, 7 * 24 * 3600)  # Max 7 days
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=presigned_expiry
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
    
    def download_file(self, object_key, password=None):
        """Download a file from MinIO storage"""
        try:
            # Get file info first
            file_info = self.get_file_info(object_key)
            if not file_info['success']:
                return file_info
            
            # Check password if required
            if file_info['has_password']:
                if not password:
                    return {'success': False, 'error': 'Password required'}
                
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash != file_info['password_hash']:
                    return {'success': False, 'error': 'Invalid password'}
            
            # Check if file has expired
            if file_info['expiry_time']:
                expiry_time = datetime.fromisoformat(file_info['expiry_time'])
                if datetime.utcnow() > expiry_time:
                    return {'success': False, 'error': 'File has expired'}
            
            # Generate presigned URL for download
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'success': True,
                'download_url': download_url,
                'filename': file_info['filename'],
                'size': file_info['size'],
                'content_type': file_info['content_type']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Download failed: {str(e)}'}
    
    def delete_file(self, object_key, user_id=None):
        """Delete a file from MinIO storage"""
        try:
            # Verify ownership if user_id provided
            if user_id:
                file_info = self.get_file_info(object_key)
                if file_info['success'] and file_info['user_id'] != user_id:
                    return {'success': False, 'error': 'Unauthorized'}
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            
            return {'success': True, 'message': 'File deleted successfully'}
            
        except ClientError as e:
            return {'success': False, 'error': f'Delete failed: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def list_user_files(self, user_id, limit=100):
        """List files uploaded by a specific user"""
        try:
            # List objects with user prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"shared/{user_id}/",
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                file_info = self.get_file_info(obj['Key'])
                if file_info['success']:
                    files.append({
                        'object_key': obj['Key'],
                        'file_id': file_info['file_id'],
                        'filename': file_info['filename'],
                        'size': file_info['size'],
                        'upload_time': file_info['upload_time'],
                        'expiry_time': file_info['expiry_time'],
                        'has_password': file_info['has_password']
                    })
            
            # Also check private files
            private_response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"private/{user_id}/",
                MaxKeys=limit
            )
            
            for obj in private_response.get('Contents', []):
                file_info = self.get_file_info(obj['Key'])
                if file_info['success']:
                    files.append({
                        'object_key': obj['Key'],
                        'file_id': file_info['file_id'],
                        'filename': file_info['filename'],
                        'size': file_info['size'],
                        'upload_time': file_info['upload_time'],
                        'expiry_time': file_info['expiry_time'],
                        'has_password': file_info['has_password']
                    })
            
            return {'success': True, 'files': files}
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to list files: {str(e)}'}
    
    def cleanup_expired_files(self):
        """Clean up expired files"""
        try:
            current_time = datetime.utcnow()
            deleted_count = 0
            
            # List all objects
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            for obj in response.get('Contents', []):
                file_info = self.get_file_info(obj['Key'])
                if file_info['success'] and file_info['expiry_time']:
                    expiry_time = datetime.fromisoformat(file_info['expiry_time'])
                    if current_time > expiry_time:
                        delete_result = self.delete_file(obj['Key'])
                        if delete_result['success']:
                            deleted_count += 1
                            print(f"Deleted expired file: {obj['Key']}")
            
            return {'success': True, 'deleted_count': deleted_count}
            
        except Exception as e:
            return {'success': False, 'error': f'Cleanup failed: {str(e)}'}
    
    def get_storage_stats(self):
        """Get storage statistics"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            total_files = 0
            total_size = 0
            
            for obj in response.get('Contents', []):
                total_files += 1
                total_size += obj['Size']
            
            return {
                'success': True,
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to get stats: {str(e)}'}

    def find_file_by_id(self, file_id):
        """
        Searches for a file by its file_id across all objects.
        NOTE: This is highly inefficient and should be replaced by a database lookup.
        """
        try:
            # List all objects in the bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            for page in pages:
                for content in page.get('Contents', []):
                    object_key = content['Key']
                    # Use head_object to get metadata and check file_id
                    try:
                        response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
                        metadata = response.get('Metadata', {})
                        
                        if metadata.get('file-id') == file_id:
                            return {'success': True, 'object_key': object_key}
                    except ClientError as e:
                        # Ignore if object is not found or other head_object error
                        pass
            
            return {'success': False, 'error': 'File not found'}
            
        except Exception as e:
            return {'success': False, 'error': f'Search failed: {str(e)}'}

# Global MinIO client instance
minio_client = MinIOClient()
