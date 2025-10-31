import hashlib
import secrets
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

from ..models.database import db
from ..models import File
from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit, strict_rate_limit

password_bp = Blueprint('password', __name__)

def generate_file_password():
    """Generate a secure random password for file protection"""
    # Generate a 12-character password with letters and numbers
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    password = ''.join(secrets.choice(alphabet) for _ in range(12))
    return password

def hash_file_password(password):
    """Hash a file password for secure storage"""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_file_password(password, password_hash):
    """Verify a file password against its hash"""
    return check_password_hash(password_hash, password)

@password_bp.route('/files/<file_id>/password', methods=['POST'])
@require_auth
@api_rate_limit
def set_file_password(file_id):
    """Set password protection for a file"""
    try:
        data = request.get_json()
        password = data.get('password')
        auto_generate = data.get('auto_generate', False)
        
        # Get the file
        file_record = File.query.filter_by(id=file_id).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Generate password if requested
        if auto_generate:
            password = generate_file_password()
        elif not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Hash and store the password
        password_hash = hash_file_password(password)
        file_record.password_hash = password_hash
        file_record.is_password_protected = True
        
        db.session.commit()
        
        response_data = {
            'message': 'Password protection enabled',
            'file_id': file_id,
            'is_password_protected': True
        }
        
        # Only return the password if it was auto-generated
        if auto_generate:
            response_data['generated_password'] = password
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'Password setup failed: {str(e)}'}), 500

@password_bp.route('/files/<file_id>/password', methods=['DELETE'])
@require_auth
@api_rate_limit
def remove_file_password(file_id):
    """Remove password protection from a file"""
    try:
        # Get the file
        file_record = File.query.filter_by(id=file_id).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Remove password protection
        file_record.password_hash = None
        file_record.is_password_protected = False
        
        db.session.commit()
        
        return jsonify({
            'message': 'Password protection removed',
            'file_id': file_id,
            'is_password_protected': False
        })
        
    except Exception as e:
        return jsonify({'error': f'Password removal failed: {str(e)}'}), 500

@password_bp.route('/files/<file_id>/verify-password', methods=['POST'])
@strict_rate_limit  # Stricter rate limiting for password attempts
def verify_file_password_endpoint(file_id):
    """Verify password for accessing a protected file"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Get the file
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file is password protected
        if not file_record.is_password_protected:
            return jsonify({'error': 'File is not password protected'}), 400
        
        # Verify password
        if not verify_file_password(password, file_record.password_hash):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Generate a temporary access token (valid for 1 hour)
        access_token = secrets.token_urlsafe(32)
        
        # Store the access token in session or cache
        # For now, we'll return it and expect the client to include it in download requests
        
        return jsonify({
            'message': 'Password verified',
            'access_token': access_token,
            'expires_in': 3600,  # 1 hour
            'file_info': {
                'id': file_record.id,
                'name': file_record.original_name,
                'size': file_record.file_size,
                'type': file_record.mime_type,
                'created_at': file_record.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Password verification failed: {str(e)}'}), 500

@password_bp.route('/files/<file_id>/password-status', methods=['GET'])
@api_rate_limit
def get_password_status(file_id):
    """Get password protection status for a file"""
    try:
        # Get the file
        file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'file_id': file_id,
            'is_password_protected': file_record.is_password_protected,
            'requires_password': file_record.is_password_protected
        })
        
    except Exception as e:
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@password_bp.route('/files/<file_id>/change-password', methods=['PUT'])
@require_auth
@api_rate_limit
def change_file_password(file_id):
    """Change password for a protected file"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Both current and new passwords are required'}), 400
        
        # Get the file
        file_record = File.query.filter_by(id=file_id).first()
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file
        if file_record.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file is password protected
        if not file_record.is_password_protected:
            return jsonify({'error': 'File is not password protected'}), 400
        
        # Verify current password
        if not verify_file_password(current_password, file_record.password_hash):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password strength
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Update password
        new_password_hash = hash_file_password(new_password)
        file_record.password_hash = new_password_hash
        
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully',
            'file_id': file_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Password change failed: {str(e)}'}), 500

@password_bp.route('/password/generate', methods=['POST'])
@api_rate_limit
def generate_password_endpoint():
    """Generate a secure password for file protection"""
    try:
        data = request.get_json() or {}
        length = data.get('length', 12)
        include_symbols = data.get('include_symbols', False)
        
        # Validate length
        if length < 6 or length > 50:
            return jsonify({'error': 'Password length must be between 6 and 50 characters'}), 400
        
        # Generate password
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        if include_symbols:
            alphabet += "!@#$%^&*"
        
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return jsonify({
            'password': password,
            'length': len(password),
            'strength': 'strong' if length >= 12 else 'medium' if length >= 8 else 'weak'
        })
        
    except Exception as e:
        return jsonify({'error': f'Password generation failed: {str(e)}'}), 500

