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
from ..models.file import File
from ..models.database import db

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
@upload_rate_limit
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
        
        # CRITICAL FIX: Save file metadata to database
        try:
            file_record = File.create_file(
                user_id=user_id,
                file_data={
                    'original_name': upload_result['filename'],
                    'file_type': upload_result['content_type'],
                    'file_size': upload_result['size'],
                    'storage_key': upload_result['object_key'],
                    'password': password if password else None
                },
                expiry_hours=expiry_hours
            )
            file_record.upload_status = 'completed'
            db.session.commit()
        except Exception as db_e:
            # If database save fails, attempt to delete from MinIO to prevent orphan
            minio_client.delete_file(upload_result['object_key'])
            print(f"Database save failed, MinIO file deleted: {db_e}")
            return jsonify({'error': 'Upload failed due to database error.'}), 500
        
        # Generate share URL
        share_url = f"/share/{file_record.id}"
        
        return jsonify({
            'success': True,
            'file_id': file_record.id,
            'filename': file_record.original_name,
            'size': file_record.file_size,
            'content_type': file_record.file_type,
            'share_url': share_url,
            'download_url': upload_result['download_url'], # This is a temporary presigned URL, but we'll use the download route
            'public_url': upload_result['public_url'],
            'expiry_time': file_record.expires_at.isoformat(),
            'has_password': bool(file_record.password_hash),
            'upload_time': file_record.created_at.isoformat()
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@upload_bp.route('/files', methods=['GET'])
@require_auth
@api_rate_limit
def list_user_files():
    """List files uploaded by the current user (using database)"""
    try:
        user_id = request.current_user_id
        limit = int(request.args.get('limit', 50))
        
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 50
        
        files = File.query.filter_by(user_id=user_id, is_deleted=False).limit(limit).all()
        
        return jsonify({
            'success': True,
            'files': [file.to_dict() for file in files],
            'count': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@upload_bp.route('/files/<file_id>', methods=['DELETE'])
@require_auth
@api_rate_limit
def delete_file(file_id):
    """Delete a file (using database)"""
    try:
        user_id = request.current_user_id
        
        file_record = File.query.filter_by(id=file_id, user_id=user_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found or unauthorized'}), 404
        
        # Delete the file from MinIO
        delete_result = minio_client.delete_file(file_record.storage_key)
        
        if not delete_result['success']:
            return jsonify({'error': delete_result['error']}), 500
        
        # Mark as deleted in database
        file_record.mark_deleted()
        
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
    """Get shared file information (public endpoint, using database)"""
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found or has been deleted/expired'}), 404
        
        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 404
        
        # Return public information only
        return jsonify({
            'success': True,
            'file_id': file_record.id,
            'filename': file_record.original_name,
            'size': file_record.file_size,
            'content_type': file_record.file_type,
            'upload_time': file_record.created_at.isoformat(),
            'expiry_time': file_record.expires_at.isoformat(),
            'has_password': bool(file_record.password_hash),
            'object_key': file_record.storage_key # Return object_key for the frontend to use in download
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get file info: {str(e)}'}), 500

@upload_bp.route('/download/<path:object_key>', methods=['GET'])
@api_rate_limit
def download_file(object_key):
    """Download a file (public endpoint with optional password, using database)"""
    try:
        password = request.args.get('password', '')
        
        file_record = File.query.filter_by(storage_key=object_key, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found or has been deleted/expired'}), 404
        
        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 404
        
        # Check password
        if file_record.password_hash and not file_record.check_password(password):
            return jsonify({
                'error': 'Password required or invalid password',
                'password_required': True
            }), 401
        
        # Generate presigned URL
        download_url = minio_client.generate_presigned_url(object_key)
        
        # Increment download count
        file_record.increment_download_count()
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': file_record.original_name,
            'size': file_record.file_size,
            'content_type': file_record.file_type
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
    """Generate a QR code for the shared file link (using database)"""
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found or has been deleted/expired'}), 404
        
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
