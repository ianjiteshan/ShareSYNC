import os
import io
import qrcode
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import magic
from PIL import Image

from ..models.database import db
from ..models import User, File, Download
from .auth import require_auth
from ..middleware.rate_limiter import upload_rate_limit, download_rate_limit, api_rate_limit

files_bp = Blueprint('files', __name__)

# File type detection
def get_file_type(file_content):
    """Detect file type using python-magic"""
    try:
        mime = magic.from_buffer(file_content, mime=True)
        return mime
    except:
        return 'application/octet-stream'

def generate_thumbnail(file_content, file_type):
    """Generate thumbnail for image files"""
    if not file_type.startswith('image/'):
        return None
    
    try:
        image = Image.open(io.BytesIO(file_content))
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save thumbnail to bytes
        thumbnail_io = io.BytesIO()
        image.save(thumbnail_io, format='JPEG', quality=85)
        return thumbnail_io.getvalue()
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None

@files_bp.route('/files/<file_id>', methods=['GET'])
@download_rate_limit
def get_file_info(file_id):
    """Get file information and download page"""
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410
        
        # Check if file can be downloaded
        if not file_record.can_download():
            return jsonify({'error': 'File cannot be downloaded'}), 403
        
        # Get download statistics
        download_stats = Download.get_file_download_stats(file_id)
        
        # Generate QR code for sharing
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/files/{file_id}"
        
        file_data = file_record.to_dict()
        file_data.update({
            'share_url': share_url,
            'download_stats': download_stats,
            'qr_code_url': f"{base_url}/api/files/{file_id}/qr",
            'file_icon': file_record.get_file_icon()
        })
        
        return jsonify(file_data)
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/qr', methods=['GET'])
@api_rate_limit
def generate_qr_code(file_id):
    """Generate QR code for file sharing"""
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Generate QR code
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/files/{file_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_io = io.BytesIO()
        qr_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'qr_code_{file_id}.png'
        )
        
    except Exception as e:
        return jsonify({'error': f'QR code generation failed: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/download', methods=['POST'])
@download_rate_limit
def download_file(file_id):
    """Download file with password protection and tracking"""
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410
        
        if not file_record.can_download():
            return jsonify({'error': 'Download limit exceeded or file unavailable'}), 403
        
        # Check password if required
        data = request.get_json() or {}
        password = data.get('password')
        
        if not file_record.check_password(password):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Create download record
        user_id = getattr(request, 'current_user_id', None)
        request_data = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'referer': request.headers.get('Referer')
        }
        
        download_record = Download.create_download_record(
            file_id=file_id,
            user_id=user_id,
            request_data=request_data
        )
        
        # Generate presigned download URL from R2
        from .upload import r2_client, R2_BUCKET_NAME
        
        download_url = r2_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': file_record.storage_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Increment download count
        file_record.increment_download_count()
        
        # Mark download as completed
        download_record.mark_completed()
        
        return jsonify({
            'download_url': download_url,
            'file_name': file_record.original_name,
            'file_size': file_record.file_size,
            'expires_in': 3600
        })
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/preview', methods=['GET'])
@api_rate_limit
def preview_file(file_id):
    """Get file preview (thumbnail for images, metadata for others)"""
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410
        
        # For images, try to generate/return thumbnail
        if file_record.file_type.startswith('image/'):
            # In a real implementation, you'd store thumbnails in R2 or cache
            # For now, return file info with preview capability flag
            return jsonify({
                'preview_available': True,
                'preview_type': 'image',
                'file_info': file_record.to_dict()
            })
        
        # For other files, return metadata
        return jsonify({
            'preview_available': False,
            'preview_type': 'metadata',
            'file_info': file_record.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/stats', methods=['GET'])
@require_auth
@api_rate_limit
def get_file_stats(file_id):
    """Get detailed file statistics (owner only)"""
    try:
        file_record = File.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get download statistics
        download_stats = Download.get_file_download_stats(file_id)
        
        # Get recent downloads
        recent_downloads = Download.query.filter_by(file_id=file_id)\
                                       .order_by(Download.created_at.desc())\
                                       .limit(10)\
                                       .all()
        
        return jsonify({
            'file_info': file_record.to_dict(include_sensitive=True),
            'download_stats': download_stats,
            'recent_downloads': [d.to_dict() for d in recent_downloads]
        })
        
    except Exception as e:
        return jsonify({'error': f'Stats retrieval failed: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/delete', methods=['DELETE'])
@require_auth
@api_rate_limit
def delete_file(file_id):
    """Delete file (owner only)"""
    try:
        file_record = File.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Mark file as deleted
        file_record.mark_deleted()
        
        # TODO: Schedule actual file deletion from R2 storage
        
        return jsonify({'message': 'File deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'File deletion failed: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/extend', methods=['POST'])
@require_auth
@api_rate_limit
def extend_file_expiry(file_id):
    """Extend file expiry (owner only)"""
    try:
        file_record = File.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        hours = data.get('hours', 24)
        
        # Validate hours (max 168 hours = 1 week)
        if hours < 1 or hours > 168:
            return jsonify({'error': 'Invalid expiry extension (1-168 hours)'}), 400
        
        # Extend expiry
        file_record.expires_at = datetime.utcnow() + timedelta(hours=hours)
        db.session.commit()
        
        return jsonify({
            'message': 'File expiry extended successfully',
            'new_expiry': file_record.expires_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Expiry extension failed: {str(e)}'}), 500

@files_bp.route('/files/<file_id>/password', methods=['POST'])
@require_auth
@api_rate_limit
def set_file_password(file_id):
    """Set or update file password (owner only)"""
    try:
        file_record = File.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        password = data.get('password')
        
        # Set password (empty string removes password)
        file_record.set_password(password if password else None)
        db.session.commit()
        
        return jsonify({
            'message': 'Password updated successfully',
            'has_password': bool(file_record.password_hash)
        })
        
    except Exception as e:
        return jsonify({'error': f'Password update failed: {str(e)}'}), 500

@files_bp.route('/files', methods=['GET'])
@require_auth
@api_rate_limit
def get_user_files():
    """Get user's uploaded files"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        files_query = File.query.filter_by(
            user_id=request.current_user_id,
            is_deleted=False
        ).order_by(File.created_at.desc())
        
        files_paginated = files_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        files_data = []
        for file_record in files_paginated.items:
            file_data = file_record.to_dict()
            file_data['download_stats'] = Download.get_file_download_stats(file_record.id)
            files_data.append(file_data)
        
        return jsonify({
            'files': files_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': files_paginated.total,
                'pages': files_paginated.pages,
                'has_next': files_paginated.has_next,
                'has_prev': files_paginated.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Files retrieval failed: {str(e)}'}), 500

