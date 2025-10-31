from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func

from ..models.database import db
from ..models import File, User
from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit

limits_bp = Blueprint('limits', __name__)

# Default limits (can be configured per user/plan)
DEFAULT_LIMITS = {
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'max_daily_uploads': 50,
    'max_storage_per_user': 1024 * 1024 * 1024,  # 1GB
    'max_files_per_user': 100,
    'max_downloads_per_file': 1000,
    'max_bandwidth_per_day': 5 * 1024 * 1024 * 1024  # 5GB
}

def get_user_limits(user_id):
    """Get limits for a specific user (can be customized based on plan)"""
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return DEFAULT_LIMITS
    
    # TODO: Implement plan-based limits
    # For now, return default limits for all users
    return DEFAULT_LIMITS

def check_file_size_limit(file_size, user_id=None):
    """Check if file size is within limits"""
    limits = get_user_limits(user_id)
    return file_size <= limits['max_file_size']

def check_daily_upload_limit(user_id):
    """Check if user has exceeded daily upload limit"""
    limits = get_user_limits(user_id)
    
    # Count uploads in the last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    daily_uploads = File.query.filter(
        File.user_id == user_id,
        File.created_at >= yesterday,
        File.is_deleted == False
    ).count()
    
    return daily_uploads < limits['max_daily_uploads']

def check_storage_limit(user_id):
    """Check if user has exceeded storage limit"""
    limits = get_user_limits(user_id)
    
    # Calculate total storage used by user
    total_storage = db.session.query(func.sum(File.file_size)).filter(
        File.user_id == user_id,
        File.is_deleted == False
    ).scalar() or 0
    
    return total_storage < limits['max_storage_per_user']

def check_file_count_limit(user_id):
    """Check if user has exceeded file count limit"""
    limits = get_user_limits(user_id)
    
    # Count active files for user
    file_count = File.query.filter(
        File.user_id == user_id,
        File.is_deleted == False
    ).count()
    
    return file_count < limits['max_files_per_user']

def get_user_usage_stats(user_id):
    """Get detailed usage statistics for a user"""
    limits = get_user_limits(user_id)
    
    # Storage usage
    total_storage = db.session.query(func.sum(File.file_size)).filter(
        File.user_id == user_id,
        File.is_deleted == False
    ).scalar() or 0
    
    # File count
    file_count = File.query.filter(
        File.user_id == user_id,
        File.is_deleted == False
    ).count()
    
    # Daily uploads
    yesterday = datetime.utcnow() - timedelta(days=1)
    daily_uploads = File.query.filter(
        File.user_id == user_id,
        File.created_at >= yesterday,
        File.is_deleted == False
    ).count()
    
    # Total downloads (across all user's files)
    total_downloads = db.session.query(func.sum(File.download_count)).filter(
        File.user_id == user_id,
        File.is_deleted == False
    ).scalar() or 0
    
    return {
        'storage': {
            'used': total_storage,
            'limit': limits['max_storage_per_user'],
            'percentage': (total_storage / limits['max_storage_per_user']) * 100,
            'remaining': limits['max_storage_per_user'] - total_storage
        },
        'files': {
            'count': file_count,
            'limit': limits['max_files_per_user'],
            'percentage': (file_count / limits['max_files_per_user']) * 100,
            'remaining': limits['max_files_per_user'] - file_count
        },
        'daily_uploads': {
            'count': daily_uploads,
            'limit': limits['max_daily_uploads'],
            'percentage': (daily_uploads / limits['max_daily_uploads']) * 100,
            'remaining': limits['max_daily_uploads'] - daily_uploads
        },
        'downloads': {
            'total': total_downloads
        }
    }

@limits_bp.route('/limits/check', methods=['POST'])
@require_auth
@api_rate_limit
def check_upload_limits():
    """Check if user can upload a file with given size"""
    try:
        data = request.get_json()
        file_size = data.get('file_size', 0)
        
        user_id = request.current_user_id
        
        # Check all limits
        checks = {
            'file_size_ok': check_file_size_limit(file_size, user_id),
            'daily_uploads_ok': check_daily_upload_limit(user_id),
            'storage_ok': check_storage_limit(user_id),
            'file_count_ok': check_file_count_limit(user_id)
        }
        
        # Overall check
        can_upload = all(checks.values())
        
        # Get detailed usage stats
        usage_stats = get_user_usage_stats(user_id)
        limits = get_user_limits(user_id)
        
        return jsonify({
            'can_upload': can_upload,
            'checks': checks,
            'usage': usage_stats,
            'limits': limits,
            'file_size': file_size
        })
        
    except Exception as e:
        return jsonify({'error': f'Limit check failed: {str(e)}'}), 500

@limits_bp.route('/limits/usage', methods=['GET'])
@require_auth
@api_rate_limit
def get_usage_stats():
    """Get current usage statistics for the user"""
    try:
        user_id = request.current_user_id
        usage_stats = get_user_usage_stats(user_id)
        limits = get_user_limits(user_id)
        
        return jsonify({
            'usage': usage_stats,
            'limits': limits,
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Usage stats retrieval failed: {str(e)}'}), 500

@limits_bp.route('/limits/global', methods=['GET'])
@api_rate_limit
def get_global_limits():
    """Get global limits (public information)"""
    try:
        return jsonify({
            'max_file_size': DEFAULT_LIMITS['max_file_size'],
            'max_file_size_mb': DEFAULT_LIMITS['max_file_size'] / (1024 * 1024),
            'max_daily_uploads': DEFAULT_LIMITS['max_daily_uploads'],
            'max_storage_per_user': DEFAULT_LIMITS['max_storage_per_user'],
            'max_storage_per_user_gb': DEFAULT_LIMITS['max_storage_per_user'] / (1024 * 1024 * 1024),
            'max_files_per_user': DEFAULT_LIMITS['max_files_per_user']
        })
        
    except Exception as e:
        return jsonify({'error': f'Global limits retrieval failed: {str(e)}'}), 500

@limits_bp.route('/limits/admin/set', methods=['POST'])
@require_auth
@api_rate_limit
def set_user_limits():
    """Set custom limits for a user (admin only)"""
    try:
        # TODO: Implement admin check
        # For now, any authenticated user can set limits (not secure)
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        new_limits = data.get('limits', {})
        
        if not target_user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Validate limits
        valid_limit_keys = set(DEFAULT_LIMITS.keys())
        provided_keys = set(new_limits.keys())
        
        if not provided_keys.issubset(valid_limit_keys):
            invalid_keys = provided_keys - valid_limit_keys
            return jsonify({'error': f'Invalid limit keys: {list(invalid_keys)}'}), 400
        
        # TODO: Store custom limits in database
        # For now, we'll just return success
        
        return jsonify({
            'message': 'User limits updated successfully',
            'user_id': target_user_id,
            'new_limits': new_limits
        })
        
    except Exception as e:
        return jsonify({'error': f'Limit setting failed: {str(e)}'}), 500

@limits_bp.route('/limits/admin/reset', methods=['POST'])
@require_auth
@api_rate_limit
def reset_user_limits():
    """Reset user limits to default (admin only)"""
    try:
        # TODO: Implement admin check
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        
        if not target_user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # TODO: Remove custom limits from database
        
        return jsonify({
            'message': 'User limits reset to default',
            'user_id': target_user_id,
            'default_limits': DEFAULT_LIMITS
        })
        
    except Exception as e:
        return jsonify({'error': f'Limit reset failed: {str(e)}'}), 500

@limits_bp.route('/limits/stats/global', methods=['GET'])
@api_rate_limit
def get_global_stats():
    """Get global platform statistics"""
    try:
        # Total files
        total_files = File.query.filter_by(is_deleted=False).count()
        
        # Total storage
        total_storage = db.session.query(func.sum(File.file_size)).filter_by(is_deleted=False).scalar() or 0
        
        # Total downloads
        total_downloads = db.session.query(func.sum(File.download_count)).filter_by(is_deleted=False).scalar() or 0
        
        # Active users (users with at least one file)
        active_users = db.session.query(func.count(func.distinct(File.user_id))).filter_by(is_deleted=False).scalar() or 0
        
        # Files uploaded today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        files_today = File.query.filter(
            File.created_at >= today,
            File.is_deleted == False
        ).count()
        
        return jsonify({
            'total_files': total_files,
            'total_storage_bytes': total_storage,
            'total_storage_gb': round(total_storage / (1024 * 1024 * 1024), 2),
            'total_downloads': total_downloads,
            'active_users': active_users,
            'files_uploaded_today': files_today,
            'average_file_size_mb': round((total_storage / total_files) / (1024 * 1024), 2) if total_files > 0 else 0
        })
        
    except Exception as e:
        return jsonify({'error': f'Global stats retrieval failed: {str(e)}'}), 500

