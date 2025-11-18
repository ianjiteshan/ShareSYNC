# backend/src/routes/upload.py

import uuid
from datetime import datetime, timedelta
import io
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import magic

from ..models.database import db
from ..models import File
from ..middleware.rate_limiter import upload_rate_limit
from ..services.minio_client import minio_client

upload_bp = Blueprint("upload", __name__, url_prefix="/api")

# --------------------------
# Helper – detect MIME type 
# --------------------------
def detect_mime(file_bytes):
    try:
        return magic.from_buffer(file_bytes, mime=True)
    except Exception:
        return "application/octet-stream"

# --------------------------
# Helper – safe filename
# --------------------------
def safe_filename(name):
    return secure_filename(name) or f"file_{uuid.uuid4().hex}"

# --------------------------
# Upload Route
# --------------------------
@upload_bp.route("/upload", methods=["POST"])
@upload_rate_limit
def upload_file():
    try:
        # --------------------------
        # Validate incoming file
        # --------------------------
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        f = request.files["file"]
        if f.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        file_bytes = f.read()
        filename = safe_filename(f.filename)
        content_type = detect_mime(file_bytes)
        size = len(file_bytes)

        # --------------------------
        # Expiry hours
        # --------------------------
        try:
            expiry_hours = int(request.form.get("expiry_hours", 24))
        except Exception:
            expiry_hours = 24

        expiry_hours = max(1, min(expiry_hours, 168))
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

        # Optional password
        password = request.form.get("password") or None

        # --------------------------
        # Generate storage key
        # --------------------------
        file_id = str(uuid.uuid4())
        object_key = f"{uuid.uuid4().hex}_{filename}"

        # --------------------------
        # Upload to MinIO
        # --------------------------
        upload_res = minio_client.upload_file(
            object_key=object_key,
            file_bytes=file_bytes,
            content_type=content_type
        )

        if not upload_res.get("success"):
            return jsonify({
                "error": "Storage upload failed",
                "detail": upload_res.get("error")
            }), 500

        # --------------------------
        # Create DB record
        # --------------------------
        new_file = File(
            id=file_id,
            user_id=getattr(request, "current_user_id", None),
            original_name=filename,
            file_type=content_type,
            file_size=size,

            storage_key=upload_res.get("object_key", object_key),
            storage_url=None,  # change if using public URLs

            # download settings
            download_limit=0,         # unlimited
            download_count=0,
            is_public=True,
            password_hash=None,

            # expiry
            expires_at=expires_at,
            auto_delete=True,

            # status
            upload_status="completed",
            is_deleted=False
        )

        if password and hasattr(new_file, "set_password"):
            new_file.set_password(password)

        db.session.add(new_file)
        db.session.commit()

        # --------------------------
        # Response
        # --------------------------
        return jsonify({
            "file_id": new_file.id,
            "filename": new_file.original_name,
            "size": new_file.file_size,
            "expiry_time": new_file.expires_at.isoformat(),
            "share_url": f"/share/{new_file.id}"
        }), 200

    except Exception as e:
        current_app.logger.exception("Upload failed")

        # Attempt cleanup if object_key created
        try:
            if 'object_key' in locals():
                minio_client.delete_file(object_key)
        except Exception:
            pass

        return jsonify({"error": f"Upload failed: {str(e)}"}), 500
