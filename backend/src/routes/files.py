import os
import io
import qrcode
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
import magic
from PIL import Image

from ..models.database import db
from ..models import User, File, Download
from .auth import require_auth
from ..middleware.rate_limiter import upload_rate_limit, download_rate_limit, api_rate_limit
from ..services.minio_client import minio_client

# 🔥 IMPORTANT: Add url_prefix so routes become /api/files/...
files_bp = Blueprint('files', __name__, url_prefix="/api")


# File type detection
def get_file_type(file_content):
    try:
        return magic.from_buffer(file_content, mime=True)
    except:
        return 'application/octet-stream'


def generate_thumbnail(file_content, file_type):
    if not file_type.startswith('image/'):
        return None
    try:
        image = Image.open(io.BytesIO(file_content))
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)

        if image.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            bg.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = bg

        thumb_io = io.BytesIO()
        image.save(thumb_io, format='JPEG', quality=85)
        return thumb_io.getvalue()
    except Exception as e:
        print("Thumbnail generation failed:", e)
        return None


# ============================================================
#  GET FILE INFO (used by DownloadPage.jsx)
# ============================================================
# PUBLIC SHARE ROUTE
@files_bp.route('/share/<file_id>', methods=['GET'])
def public_share_info(file_id):
    """
    Public endpoint used by DownloadPage.jsx
    Returns basic file info without requiring authentication.
    """
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410

        # What DownloadPage.jsx expects:
        return jsonify({
            "id": file_record.id,
            "original_name": file_record.original_name,
            "file_size": file_record.file_size,
            "expires_at": file_record.expires_at.isoformat(),
            "has_password": bool(file_record.password_hash),
        })

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@files_bp.route('/files/<file_id>', methods=['GET'])
@download_rate_limit
def get_file_info(file_id):
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410

        if not file_record.can_download():
            return jsonify({'error': 'File cannot be downloaded'}), 403

        download_stats = Download.get_file_download_stats(file_id)

        # Generate share + QR URL
        # Use RELATIVE URL so frontend proxy handles it
        share_url = f"/share/{file_id}"
        qr_url = f"/api/files/{file_id}/qr"

        file_data = file_record.to_dict()
        file_data.update({
            "share_url": share_url,
            "download_stats": download_stats,
            "qr_code_url": qr_url,
            "file_icon": file_record.get_file_icon()
        })

        return jsonify(file_data)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ============================================================
#  GENERATE QR CODE (image displayed in UploadPage.jsx)
# ============================================================
@files_bp.route('/files/<file_id>/qr', methods=['GET'])
@api_rate_limit
def generate_qr_code(file_id):
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        # Generate QR to share link
        full_share_url = request.host_url.rstrip("/") + f"/share/{file_id}"

        qr = qrcode.QRCode(
            version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10, border=4,
        )
        qr.add_data(full_share_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_io = io.BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"QR code generation failed: {str(e)}"}), 500


# ============================================================
#  DOWNLOAD FILE
# ============================================================
@files_bp.route('/files/<file_id>/download', methods=['POST'])
@download_rate_limit
def download_file(file_id):
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410

        if not file_record.can_download():
            return jsonify({'error': 'Download limit exceeded'}), 403

        data = request.get_json() or {}
        password = data.get('password')

        if not file_record.check_password(password):
            return jsonify({'error': 'Invalid password'}), 401

        user_id = getattr(request, 'current_user_id', None)
        request_data = {
            "ip": request.remote_addr,
            "ua": request.headers.get("User-Agent")
        }

        download_record = Download.create_download_record(
            file_id=file_id,
            user_id=user_id,
            request_data=request_data
        )

        presigned_url = minio_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": minio_client.bucket_name, "Key": file_record.storage_key},
            ExpiresIn=3600
        )

        file_record.increment_download_count()
        download_record.mark_completed()

        return jsonify({
            "download_url": presigned_url,
            "file_name": file_record.original_name,
            "file_size": file_record.file_size
        })

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500


# ============================================================
# PREVIEW (optional)
# ============================================================
@files_bp.route('/files/<file_id>/preview', methods=['GET'])
@api_rate_limit
def preview_file(file_id):
    try:
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        if file_record.is_expired():
            return jsonify({'error': 'File has expired'}), 410

        return jsonify({
            "preview_available": file_record.file_type.startswith("image/"),
            "file_info": file_record.to_dict()
        })

    except Exception as e:
        return jsonify({"error": f"Preview failed: {str(e)}"}), 500


# ============================================================
# USER'S FILES
# ============================================================
@files_bp.route('/files', methods=['GET'])
@require_auth
@api_rate_limit
def get_user_files():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        files_query = File.query.filter_by(
            user_id=request.current_user_id,
            is_deleted=False
        ).order_by(File.created_at.desc())

        files_paginated = files_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        files_data = []
        for file_record in files_paginated.items:
            d = file_record.to_dict()
            d['download_stats'] = Download.get_file_download_stats(file_record.id)
            files_data.append(d)

        return jsonify({
            "files": files_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": files_paginated.total,
                "pages": files_paginated.pages
            }
        })

    except Exception as e:
        return jsonify({"error": f"Files retrieval failed: {str(e)}"}), 500
