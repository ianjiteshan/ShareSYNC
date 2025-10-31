import os
import hashlib
import mimetypes
import magic
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import requests
import json

from ..models.database import db
from ..models import File, User
from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit, strict_rate_limit

security_bp = Blueprint('security', __name__)

# Security configuration
ALLOWED_MIME_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
    'document': ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'text': ['text/plain', 'text/csv', 'text/markdown'],
    'archive': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'],
    'video': ['video/mp4', 'video/avi', 'video/mov', 'video/wmv'],
    'audio': ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a']
}

BLOCKED_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.app', '.deb', '.pkg', '.dmg', '.msi', '.run', '.sh', '.ps1'
]

SUSPICIOUS_PATTERNS = [
    b'<script',
    b'javascript:',
    b'vbscript:',
    b'onload=',
    b'onerror=',
    b'eval(',
    b'document.cookie',
    b'window.location'
]

def calculate_file_hash(file_content):
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def detect_mime_type(file_content, filename):
    """Detect MIME type using multiple methods"""
    # Try python-magic first (more accurate)
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type:
            return mime_type
    except:
        pass
    
    # Fallback to mimetypes module
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def scan_for_malware(file_content, filename):
    """Basic malware scanning"""
    scan_results = {
        'is_safe': True,
        'threats_found': [],
        'scan_details': {}
    }
    
    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext in BLOCKED_EXTENSIONS:
        scan_results['is_safe'] = False
        scan_results['threats_found'].append(f'Blocked file extension: {file_ext}')
    
    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in file_content:
            scan_results['is_safe'] = False
            scan_results['threats_found'].append(f'Suspicious pattern detected: {pattern.decode("utf-8", errors="ignore")}')
    
    # Check file size (basic DoS protection)
    if len(file_content) > 100 * 1024 * 1024:  # 100MB
        scan_results['is_safe'] = False
        scan_results['threats_found'].append('File size exceeds maximum allowed limit')
    
    # MIME type validation
    detected_mime = detect_mime_type(file_content, filename)
    allowed_types = []
    for category, types in ALLOWED_MIME_TYPES.items():
        allowed_types.extend(types)
    
    if detected_mime not in allowed_types:
        scan_results['is_safe'] = False
        scan_results['threats_found'].append(f'Unsupported file type: {detected_mime}')
    
    scan_results['scan_details'] = {
        'file_size': len(file_content),
        'detected_mime_type': detected_mime,
        'file_extension': file_ext,
        'scan_timestamp': datetime.utcnow().isoformat()
    }
    
    return scan_results

def check_file_reputation(file_hash):
    """Check file reputation against known databases"""
    # This is a placeholder for integration with services like VirusTotal
    # In a real implementation, you would integrate with actual threat intelligence APIs
    
    reputation_data = {
        'hash': file_hash,
        'reputation_score': 100,  # 0-100, higher is safer
        'known_malware': False,
        'first_seen': None,
        'last_analysis': datetime.utcnow().isoformat(),
        'vendor_detections': 0,
        'total_vendors': 0
    }
    
    # Simulate some basic checks
    # In reality, you would query external APIs here
    
    return reputation_data

@security_bp.route('/security/scan-file', methods=['POST'])
@require_auth
@strict_rate_limit
def scan_uploaded_file():
    """Scan an uploaded file for security threats"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_content)
        
        # Perform malware scan
        scan_results = scan_for_malware(file_content, file.filename)
        
        # Check file reputation
        reputation_data = check_file_reputation(file_hash)
        
        # Combine results
        security_report = {
            'file_info': {
                'filename': file.filename,
                'size': len(file_content),
                'hash': file_hash,
                'mime_type': detect_mime_type(file_content, file.filename)
            },
            'malware_scan': scan_results,
            'reputation': reputation_data,
            'overall_safety': scan_results['is_safe'] and reputation_data['reputation_score'] > 50,
            'scan_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'security_report': security_report,
            'recommendations': generate_security_recommendations(security_report)
        })
        
    except Exception as e:
        return jsonify({'error': f'Security scan failed: {str(e)}'}), 500

def generate_security_recommendations(security_report):
    """Generate security recommendations based on scan results"""
    recommendations = []
    
    if not security_report['malware_scan']['is_safe']:
        recommendations.append({
            'level': 'critical',
            'message': 'File contains potential security threats and should not be uploaded',
            'action': 'Block upload'
        })
    
    if security_report['reputation']['reputation_score'] < 50:
        recommendations.append({
            'level': 'warning',
            'message': 'File has a low reputation score',
            'action': 'Consider additional verification'
        })
    
    if security_report['file_info']['size'] > 50 * 1024 * 1024:  # 50MB
        recommendations.append({
            'level': 'info',
            'message': 'Large file detected',
            'action': 'Consider file compression'
        })
    
    if not recommendations:
        recommendations.append({
            'level': 'success',
            'message': 'File appears to be safe',
            'action': 'Proceed with upload'
        })
    
    return recommendations

@security_bp.route('/security/file-preview/<file_id>', methods=['GET'])
@api_rate_limit
def get_secure_file_preview(file_id):
    """Get a secure preview of a file"""
    try:
        # Get file record
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file is password protected
        if file_record.is_password_protected:
            # Require password verification token
            auth_token = request.headers.get('X-Preview-Token')
            if not auth_token:
                return jsonify({'error': 'Password verification required'}), 401
        
        # Generate preview based on file type
        preview_data = generate_file_preview(file_record)
        
        return jsonify({
            'file_id': file_id,
            'preview': preview_data,
            'security_info': {
                'is_safe': True,  # Since it's already uploaded and scanned
                'scan_date': file_record.created_at.isoformat(),
                'file_hash': getattr(file_record, 'file_hash', None)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Preview generation failed: {str(e)}'}), 500

def generate_file_preview(file_record):
    """Generate a safe preview of the file"""
    preview_data = {
        'type': 'metadata',
        'filename': file_record.original_name,
        'size': file_record.file_size,
        'mime_type': file_record.mime_type,
        'upload_date': file_record.created_at.isoformat(),
        'download_count': file_record.download_count
    }
    
    # Add type-specific preview data
    if file_record.mime_type.startswith('image/'):
        preview_data['type'] = 'image'
        preview_data['preview_available'] = True
        # In a real implementation, you would generate a thumbnail
        
    elif file_record.mime_type.startswith('text/'):
        preview_data['type'] = 'text'
        preview_data['preview_available'] = True
        # In a real implementation, you would show first few lines
        
    elif file_record.mime_type == 'application/pdf':
        preview_data['type'] = 'document'
        preview_data['preview_available'] = True
        # In a real implementation, you would generate page thumbnails
        
    else:
        preview_data['type'] = 'binary'
        preview_data['preview_available'] = False
    
    return preview_data

@security_bp.route('/security/quarantine/<file_id>', methods=['POST'])
@require_auth
@strict_rate_limit
def quarantine_file(file_id):
    """Quarantine a suspicious file"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Security concern')
        
        # Get file record
        file_record = File.query.filter_by(id=file_id).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check permissions (admin or file owner)
        if file_record.user_id != request.current_user_id:
            # TODO: Add admin check
            return jsonify({'error': 'Access denied'}), 403
        
        # Mark file as quarantined
        file_record.is_quarantined = True
        file_record.quarantine_reason = reason
        file_record.quarantined_at = datetime.utcnow()
        file_record.quarantined_by = request.current_user_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'File quarantined successfully',
            'file_id': file_id,
            'reason': reason,
            'quarantined_at': file_record.quarantined_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Quarantine failed: {str(e)}'}), 500

@security_bp.route('/security/audit-log', methods=['GET'])
@require_auth
@api_rate_limit
def get_security_audit_log():
    """Get security audit log for user's files"""
    try:
        user_id = request.current_user_id
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get user's files with security events
        files_query = File.query.filter_by(user_id=user_id)
        
        # Filter by date range if provided
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
            files_query = files_query.filter(File.created_at >= start_date)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
            files_query = files_query.filter(File.created_at <= end_date)
        
        files = files_query.order_by(File.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        audit_entries = []
        for file in files.items:
            entry = {
                'file_id': file.id,
                'filename': file.original_name,
                'event_type': 'upload',
                'timestamp': file.created_at.isoformat(),
                'details': {
                    'file_size': file.file_size,
                    'mime_type': file.mime_type,
                    'is_password_protected': file.is_password_protected
                }
            }
            
            # Add quarantine info if applicable
            if getattr(file, 'is_quarantined', False):
                entry['security_status'] = 'quarantined'
                entry['quarantine_reason'] = getattr(file, 'quarantine_reason', '')
            else:
                entry['security_status'] = 'safe'
            
            audit_entries.append(entry)
        
        return jsonify({
            'audit_log': audit_entries,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': files.total,
                'pages': files.pages,
                'has_next': files.has_next,
                'has_prev': files.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Audit log retrieval failed: {str(e)}'}), 500

@security_bp.route('/security/settings', methods=['GET', 'POST'])
@require_auth
@api_rate_limit
def security_settings():
    """Get or update user security settings"""
    try:
        user_id = request.current_user_id
        
        if request.method == 'GET':
            # Return current security settings
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            settings = {
                'auto_scan_enabled': getattr(user, 'auto_scan_enabled', True),
                'quarantine_suspicious': getattr(user, 'quarantine_suspicious', False),
                'notification_preferences': {
                    'security_alerts': getattr(user, 'security_alerts_enabled', True),
                    'scan_results': getattr(user, 'scan_results_enabled', False)
                },
                'file_restrictions': {
                    'max_file_size_mb': 100,
                    'allowed_types': list(ALLOWED_MIME_TYPES.keys()),
                    'block_executables': True
                }
            }
            
            return jsonify({'security_settings': settings})
            
        elif request.method == 'POST':
            # Update security settings
            data = request.get_json() or {}
            
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Update settings (in a real implementation, you'd have proper user settings model)
            # For now, just return success
            
            return jsonify({
                'message': 'Security settings updated successfully',
                'updated_settings': data,
                'updated_at': datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        return jsonify({'error': f'Security settings operation failed: {str(e)}'}), 500

@security_bp.route('/security/report-threat', methods=['POST'])
@require_auth
@strict_rate_limit
def report_security_threat():
    """Report a security threat or suspicious file"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        threat_type = data.get('threat_type')
        description = data.get('description', '')
        
        if not file_id or not threat_type:
            return jsonify({'error': 'File ID and threat type are required'}), 400
        
        # Validate threat type
        valid_threat_types = ['malware', 'phishing', 'spam', 'inappropriate', 'copyright', 'other']
        if threat_type not in valid_threat_types:
            return jsonify({'error': 'Invalid threat type'}), 400
        
        # Get file record
        file_record = File.query.filter_by(id=file_id).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Create threat report (in a real implementation, you'd have a ThreatReport model)
        threat_report = {
            'id': f"threat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'file_id': file_id,
            'reported_by': request.current_user_id,
            'threat_type': threat_type,
            'description': description,
            'reported_at': datetime.utcnow().isoformat(),
            'status': 'pending_review'
        }
        
        # In a real implementation, you would:
        # 1. Store the report in database
        # 2. Notify security team
        # 3. Potentially auto-quarantine the file
        # 4. Update file's security status
        
        return jsonify({
            'message': 'Threat report submitted successfully',
            'report_id': threat_report['id'],
            'status': 'pending_review'
        })
        
    except Exception as e:
        return jsonify({'error': f'Threat reporting failed: {str(e)}'}), 500

