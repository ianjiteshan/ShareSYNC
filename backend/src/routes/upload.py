import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import boto3
from botocore.exceptions import ClientError
from .auth import require_auth
from ..middleware.rate_limiter import upload_rate_limit, download_rate_limit, api_rate_limit

upload_bp = Blueprint('upload', __name__)

# Cloudflare R2 configuration (set these environment variables)
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID', 'your-account-id')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', 'your-access-key')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', 'your-secret-key')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'sharesync-files')

# Initialize R2 client
r2_client = boto3.client(
    's3',
    endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name='auto'
)

# In-memory storage for file metadata (use database in production)
file_metadata = {}

@upload_bp.route('/upload/presigned-url', methods=['POST'])
@require_auth
@upload_rate_limit
def get_presigned_upload_url():
    """Generate presigned URL for direct upload to R2"""
    try:
        data = request.get_json()
        
        # Validate request data
        if not data or 'fileName' not in data or 'fileType' not in data:
            return jsonify({'error': 'Missing fileName or fileType'}), 400
        
        file_name = data['fileName']
        file_type = data['fileType']
        file_size = data.get('fileSize', 0)
        expiry_hours = data.get('expiryHours', 24)
        
        # Generate unique file key
        file_id = str(uuid.uuid4())
        file_key = f"{file_id}/{file_name}"
        
        # Generate presigned URL for upload
        presigned_url = r2_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': R2_BUCKET_NAME,
                'Key': file_key,
                'ContentType': file_type
            },
            ExpiresIn=3600  # 1 hour to complete upload
        )
        
        # Store metadata
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        file_metadata[file_id] = {
            'id': file_id,
            'key': file_key,
            'original_name': file_name,
            'file_type': file_type,
            'file_size': file_size,
            'expires_at': expires_at.isoformat(),
            'uploaded': False,
            'created_at': datetime.utcnow().isoformat(),
            'user_id': request.current_user_id  # Add user ID from auth decorator
        }
        
        return jsonify({
            'fileId': file_id,
            'uploadUrl': presigned_url,
            'key': file_key
        })
        
    except ClientError as e:
        return jsonify({'error': f'R2 error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@upload_bp.route('/upload/complete', methods=['POST'])
@require_auth
@api_rate_limit
def complete_upload():
    """Mark upload as complete and generate share link"""
    try:
        data = request.get_json()
        
        if not data or 'fileId' not in data:
            return jsonify({'error': 'Missing fileId'}), 400
        
        file_id = data['fileId']
        
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        # Mark as uploaded
        file_metadata[file_id]['uploaded'] = True
        
        # Generate share link
        share_link = f"/share/{file_id}"
        
        return jsonify({
            'shareLink': share_link,
            'fileId': file_id,
            'expiresAt': file_metadata[file_id]['expires_at']
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@upload_bp.route('/upload/download/<file_id>', methods=['GET'])
@download_rate_limit
def get_download_url(file_id):
    """Generate presigned URL for file download"""
    try:
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        metadata = file_metadata[file_id]
        
        # Check if file has expired
        expires_at = datetime.fromisoformat(metadata['expires_at'])
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'File has expired'}), 410
        
        if not metadata['uploaded']:
            return jsonify({'error': 'File upload not completed'}), 400
        
        # Generate presigned URL for download
        download_url = r2_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': R2_BUCKET_NAME,
                'Key': metadata['key'],
                'ResponseContentDisposition': f'attachment; filename="{metadata["original_name"]}"'
            },
            ExpiresIn=600  # 10 minutes to download
        )
        
        return jsonify({
            'downloadUrl': download_url,
            'fileName': metadata['original_name'],
            'fileSize': metadata['file_size'],
            'expiresAt': metadata['expires_at']
        })
        
    except ClientError as e:
        return jsonify({'error': f'R2 error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@upload_bp.route('/upload/info/<file_id>', methods=['GET'])
@api_rate_limit
def get_file_info(file_id):
    """Get file information"""
    try:
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        metadata = file_metadata[file_id]
        
        # Check if file has expired
        expires_at = datetime.fromisoformat(metadata['expires_at'])
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'File has expired'}), 410
        
        return jsonify({
            'fileId': file_id,
            'fileName': metadata['original_name'],
            'fileSize': metadata['file_size'],
            'fileType': metadata['file_type'],
            'expiresAt': metadata['expires_at'],
            'uploaded': metadata['uploaded']
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@upload_bp.route('/upload/cleanup', methods=['POST'])
def cleanup_expired_files():
    """Clean up expired files (call this periodically)"""
    try:
        current_time = datetime.utcnow()
        expired_files = []
        
        for file_id, metadata in list(file_metadata.items()):
            expires_at = datetime.fromisoformat(metadata['expires_at'])
            if current_time > expires_at:
                # Delete from R2
                try:
                    r2_client.delete_object(
                        Bucket=R2_BUCKET_NAME,
                        Key=metadata['key']
                    )
                except ClientError:
                    pass  # File might not exist in R2
                
                # Remove from metadata
                expired_files.append(file_id)
                del file_metadata[file_id]
        
        return jsonify({
            'message': f'Cleaned up {len(expired_files)} expired files',
            'expired_files': expired_files
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

