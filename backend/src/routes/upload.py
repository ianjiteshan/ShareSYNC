import os
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import hashlib
import qrcode
import base64
from io import BytesIO

from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit, upload_rate_limit
from ..services.minio_client import minio_client

upload_bp = Blueprint('upload', __name__)

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 
    'ppt', 'pptx', 'zip', 'rar', '7z', 'mp3', 'mp4', 'avi', 'mov', 'wmv',
    'flv', 'webm', 'mkv', 'wav', 'flac', 'aac', 'ogg', 'svg', 'bmp', 'tiff',
    'ico', 'webp', 'csv', 'json', 'xml', 'html', 'css', 'js', 'py', 'java',
    'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'scala'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_obj):
    """Get file size"""
    file_obj.seek(0, 2)  # Seek to end
    size = file_obj.tell()
    file_obj.seek(0)  # Reset to beginning
    return size

@upload_bp.route('/upload', methods=['POST'])
@require_auth
#@upload_rate_limit
def upload_file():
    """Upload a file to MinIO storage"""
    try:
        user_id = request.current_user_id
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Check file size
        file_size = get_file_size(file)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        if file_size == 0:
            return jsonify({'error': 'Empty file not allowed'}), 400
        
        # Get upload options
        expiry_hours = int(request.form.get('expiry_hours', 24))
        password = request.form.get('password', '').strip()
        
        # Validate expiry hours (1 hour to 7 days)
        if expiry_hours < 1 or expiry_hours > 168:
            return jsonify({'error': 'Expiry must be between 1 hour and 7 days'}), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"file_{uuid.uuid4().hex[:8]}"
        
        # Upload to MinIO
        upload_result = minio_client.upload_file(
            file_obj=file,
            filename=filename,
            user_id=user_id,
            expiry_hours=expiry_hours,
            password=password if password else None
        )
        
        if not upload_result['success']:
            return jsonify({'error': upload_result['error']}), 500
        
        # Generate share URL
        share_url = f"/share/{upload_result['file_id']}"
        
        return jsonify({
            'success': True,
            'file_id': upload_result['file_id'],
            'filename': upload_result['filename'],
            'size': upload_result['size'],
            'content_type': upload_result['content_type'],
            'share_url': share_url,
            'download_url': upload_result['download_url'],
            'public_url': upload_result['public_url'],
            'expiry_time': upload_result['expiry_time'],
            'has_password': upload_result['has_password'],
            'upload_time': upload_result['upload_time']
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@upload_bp.route('/files', methods=['GET'])
@require_auth
@api_rate_limit
def list_user_files():
    """List files uploaded by the current user"""
    try:
        user_id = request.current_user_id
        limit = int(request.args.get('limit', 50))
        
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 50
        
        result = minio_client.list_user_files(user_id, limit)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        return jsonify({
            'success': True,
            'files': result['files'],
            'count': len(result['files'])
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@upload_bp.route('/files/<file_id>', methods=['DELETE'])
@require_auth
@api_rate_limit
def delete_file(file_id):
    """Delete a file"""
    try:
        user_id = request.current_user_id
        
        # Find the file by ID (we need to search through user's files)
        files_result = minio_client.list_user_files(user_id, 1000)
        if not files_result['success']:
            return jsonify({'error': 'Failed to find file'}), 500
        
        # Find the file with matching ID
        target_file = None
        for file_info in files_result['files']:
            if file_info['file_id'] == file_id:
                target_file = file_info
                break
        
        if not target_file:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete the file
        delete_result = minio_client.delete_file(target_file['object_key'], user_id)
        
        if not delete_result['success']:
            return jsonify({'error': delete_result['error']}), 500
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully',
            'file_id': file_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@upload_bp.route('/share/<file_id>', methods=['GET'])
@api_rate_limit
def get_shared_file(file_id):
    """Get shared file information (public endpoint)"""
    try:
        # Search for the file across all users (this is not efficient for large scale)
        # In production, you'd want a database to map file_id to object_key
        
        # This is a temporary, inefficient solution. In a production app,
        # a database should map file_id to object_key for fast lookup.
        
        # Search for the file by ID across all users (up to 1000 files total)
        search_result = minio_client.find_file_by_id(file_id)
        
        if not search_result['success']:
            return jsonify({'error': search_result['error']}), 404
        
        object_key = search_result['object_key']
        
        # Now get the file info
        file_info = minio_client.get_file_info(object_key)
        
        if not file_info['success']:
            return jsonify({'error': file_info['error']}), 404
        
        # Return public information only
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': file_info['filename'],
            'size': file_info['size'],
            'content_type': file_info['content_type'],
            'upload_time': file_info['upload_time'],
            'expiry_time': file_info['expiry_time'],
            'has_password': file_info['has_password'],
            'object_key': object_key # Return object_key for the frontend to use in download
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get file info: {str(e)}'}), 500

@upload_bp.route('/download/<path:object_key>', methods=['GET'])
@api_rate_limit
def download_file(object_key):
    """Download a file (public endpoint with optional password)"""
    try:
        password = request.args.get('password', '')
        
        download_result = minio_client.download_file(
            object_key=object_key,
            password=password if password else None
        )
        
        if not download_result['success']:
            if 'Password required' in download_result['error']:
                return jsonify({
                    'error': download_result['error'],
                    'password_required': True
                }), 401
            return jsonify({'error': download_result['error']}), 400
        
        return jsonify({
            'success': True,
            'download_url': download_result['download_url'],
            'filename': download_result['filename'],
            'size': download_result['size'],
            'content_type': download_result['content_type']
        })
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@upload_bp.route('/file-info/<path:object_key>', methods=['GET'])
@api_rate_limit
def get_file_info(object_key):
    """Get file information (public endpoint)"""
    try:
        file_info = minio_client.get_file_info(object_key)
        
        if not file_info['success']:
            return jsonify({'error': file_info['error']}), 404
        
        # Return public information only
        return jsonify({
            'success': True,
            'filename': file_info['filename'],
            'size': file_info['size'],
            'content_type': file_info['content_type'],
            'upload_time': file_info['upload_time'],
            'expiry_time': file_info['expiry_time'],
            'has_password': file_info['has_password']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get file info: {str(e)}'}), 500

@upload_bp.route('/storage-stats', methods=['GET'])
@require_auth
@api_rate_limit
def get_storage_stats():
    """Get storage statistics for the current user"""
    try:
        user_id = request.current_user_id
        
        # Get user's files
        files_result = minio_client.list_user_files(user_id, 1000)
        if not files_result['success']:
            return jsonify({'error': files_result['error']}), 500
        
        # Calculate user statistics
        total_files = len(files_result['files'])
        total_size = sum(file_info['size'] for file_info in files_result['files'])
        
        # Get global stats (admin only - for now return user stats)
        global_stats = minio_client.get_storage_stats()
        
        return jsonify({
            'success': True,
            'user_stats': {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            },
            'global_stats': global_stats if global_stats['success'] else None
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@upload_bp.route('/qr-code/<file_id>', methods=['GET'])
@api_rate_limit
def generate_qr_code(file_id):
    """Generate a QR code for the shared file link"""
    try:
        # This is a temporary, inefficient solution. In a production app,
        # a database should map file_id to object_key for fast lookup.
        search_result = minio_client.find_file_by_id(file_id)
        
        if not search_result['success']:
            return jsonify({'error': search_result['error']}), 404
        
        # Construct the full share URL (assuming the frontend is served from the root)
        share_url = f"{request.host_url.rstrip('/')}/share/{file_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to a byte buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        # Encode to base64
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'qr_code_base64': qr_base64,
            'share_url': share_url
        })
        
    except Exception as e:
        print(f"QR code generation failed: {e}")
        return jsonify({'error': f'QR code generation failed: {str(e)}'}), 500

@upload_bp.route('/cleanup-expired', methods=['POST'])
@require_auth
@api_rate_limit
def cleanup_expired_files():
    """Clean up expired files (admin function)"""
    try:
        # In a real app, you'd check if user is admin
        # For now, any authenticated user can trigger cleanup
        
        cleanup_result = minio_client.cleanup_expired_files()
        
        if not cleanup_result['success']:
            return jsonify({'error': cleanup_result['error']}), 500
        
        return jsonify({
            'success': True,
            'message': f"Cleaned up {cleanup_result['deleted_count']} expired files"
        })
        
    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500
