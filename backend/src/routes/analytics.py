from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc

from ..models.database import db
from ..models import User, File, Download
from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/dashboard', methods=['GET'])
@require_auth
@api_rate_limit
def get_user_dashboard():
    """Get user dashboard analytics"""
    try:
        user_id = request.current_user_id
        
        # Get user upload statistics
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        upload_stats = user.get_upload_stats()
        
        # Get recent files
        recent_files = File.query.filter_by(user_id=user_id, is_deleted=False)\
                                .order_by(File.created_at.desc())\
                                .limit(5)\
                                .all()
        
        # Get download history
        recent_downloads = Download.get_user_download_history(user_id, limit=10)
        
        # Get popular files
        popular_files_data = db.session.query(
            File.id,
            File.original_name,
            File.file_type,
            File.created_at,
            func.count(Download.id).label('download_count')
        ).join(Download, File.id == Download.file_id)\
         .filter(File.user_id == user_id, File.is_deleted == False)\
         .group_by(File.id)\
         .order_by(desc('download_count'))\
         .limit(5)\
         .all()
        
        # Format popular files
        popular_files = []
        for file_data in popular_files_data:
            popular_files.append({
                'id': file_data.id,
                'name': file_data.original_name,
                'type': file_data.file_type,
                'created_at': file_data.created_at.isoformat(),
                'download_count': file_data.download_count
            })
        
        # Get weekly upload trend
        weekly_trend = []
        for i in range(7):
            date = datetime.utcnow().date() - timedelta(days=i)
            count = File.query.filter(
                File.user_id == user_id,
                func.date(File.created_at) == date
            ).count()
            weekly_trend.append({
                'date': date.isoformat(),
                'uploads': count
            })
        
        return jsonify({
            'user_info': user.to_dict(),
            'upload_stats': upload_stats,
            'recent_files': [f.to_dict() for f in recent_files],
            'recent_downloads': [d.to_dict() for d in recent_downloads],
            'popular_files': popular_files,
            'weekly_trend': list(reversed(weekly_trend))
        })
        
    except Exception as e:
        return jsonify({'error': f'Dashboard data retrieval failed: {str(e)}'}), 500

@analytics_bp.route('/analytics/platform', methods=['GET'])
@api_rate_limit
def get_platform_analytics():
    """Get public platform analytics"""
    try:
        # Basic platform statistics
        total_users = User.query.count()
        total_files = File.query.filter_by(is_deleted=False).count()
        total_downloads = Download.query.filter_by(download_status='completed').count()
        
        # Files uploaded in the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        files_24h = File.query.filter(File.created_at >= yesterday).count()
        
        # Total storage used (in MB)
        total_storage = db.session.query(func.sum(File.file_size)).filter_by(is_deleted=False).scalar() or 0
        total_storage_mb = round(total_storage / (1024 * 1024), 2)
        
        # Most popular file types
        popular_types = db.session.query(
            File.file_type,
            func.count(File.id).label('count')
        ).filter_by(is_deleted=False)\
         .group_by(File.file_type)\
         .order_by(desc('count'))\
         .limit(10)\
         .all()
        
        file_types = [{'type': ft.file_type, 'count': ft.count} for ft in popular_types]
        
        # Daily upload trend (last 30 days)
        daily_trend = []
        for i in range(30):
            date = datetime.utcnow().date() - timedelta(days=i)
            count = File.query.filter(func.date(File.created_at) == date).count()
            daily_trend.append({
                'date': date.isoformat(),
                'uploads': count
            })
        
        return jsonify({
            'platform_stats': {
                'total_users': total_users,
                'total_files': total_files,
                'total_downloads': total_downloads,
                'files_24h': files_24h,
                'total_storage_mb': total_storage_mb
            },
            'popular_file_types': file_types,
            'daily_trend': list(reversed(daily_trend))
        })
        
    except Exception as e:
        return jsonify({'error': f'Platform analytics retrieval failed: {str(e)}'}), 500

@analytics_bp.route('/analytics/file/<file_id>', methods=['GET'])
@require_auth
@api_rate_limit
def get_file_analytics(file_id):
    """Get detailed analytics for a specific file"""
    try:
        # Check if user owns the file
        file_record = File.query.filter_by(id=file_id, user_id=request.current_user_id).first()
        if not file_record:
            return jsonify({'error': 'File not found or access denied'}), 404
        
        # Get download statistics
        download_stats = Download.get_file_download_stats(file_id)
        
        # Get download timeline (last 30 days)
        download_timeline = []
        for i in range(30):
            date = datetime.utcnow().date() - timedelta(days=i)
            count = Download.query.filter(
                Download.file_id == file_id,
                func.date(Download.created_at) == date,
                Download.download_status == 'completed'
            ).count()
            download_timeline.append({
                'date': date.isoformat(),
                'downloads': count
            })
        
        # Get geographic distribution (if available)
        geo_stats = db.session.query(
            Download.country,
            func.count(Download.id).label('count')
        ).filter(
            Download.file_id == file_id,
            Download.country.isnot(None)
        ).group_by(Download.country)\
         .order_by(desc('count'))\
         .limit(10)\
         .all()
        
        geographic_data = [{'country': gs.country, 'downloads': gs.count} for gs in geo_stats]
        
        # Get referrer statistics
        referrer_stats = db.session.query(
            Download.referer,
            func.count(Download.id).label('count')
        ).filter(
            Download.file_id == file_id,
            Download.referer.isnot(None)
        ).group_by(Download.referer)\
         .order_by(desc('count'))\
         .limit(10)\
         .all()
        
        referrer_data = [{'referrer': rs.referer, 'downloads': rs.count} for rs in referrer_stats]
        
        return jsonify({
            'file_info': file_record.to_dict(),
            'download_stats': download_stats,
            'download_timeline': list(reversed(download_timeline)),
            'geographic_distribution': geographic_data,
            'referrer_stats': referrer_data
        })
        
    except Exception as e:
        return jsonify({'error': f'File analytics retrieval failed: {str(e)}'}), 500

@analytics_bp.route('/analytics/export', methods=['POST'])
@require_auth
@api_rate_limit
def export_analytics():
    """Export user analytics data"""
    try:
        user_id = request.current_user_id
        data = request.get_json()
        export_type = data.get('type', 'csv')  # csv, json
        date_range = data.get('date_range', 30)  # days
        
        # Validate date range
        if date_range > 365:
            return jsonify({'error': 'Date range cannot exceed 365 days'}), 400
        
        start_date = datetime.utcnow() - timedelta(days=date_range)
        
        # Get user files and downloads in date range
        files = File.query.filter(
            File.user_id == user_id,
            File.created_at >= start_date
        ).all()
        
        downloads = Download.query.join(File).filter(
            File.user_id == user_id,
            Download.created_at >= start_date
        ).all()
        
        if export_type == 'json':
            export_data = {
                'export_date': datetime.utcnow().isoformat(),
                'date_range_days': date_range,
                'files': [f.to_dict(include_sensitive=True) for f in files],
                'downloads': [d.to_dict() for d in downloads]
            }
            
            return jsonify(export_data)
        
        else:  # CSV format
            import csv
            import io
            
            output = io.StringIO()
            
            # Write files data
            writer = csv.writer(output)
            writer.writerow(['File ID', 'Name', 'Type', 'Size (MB)', 'Downloads', 'Created', 'Expires'])
            
            for file in files:
                stats = Download.get_file_download_stats(file.id)
                writer.writerow([
                    file.id,
                    file.original_name,
                    file.file_type,
                    round(file.file_size / (1024 * 1024), 2),
                    stats['completed_downloads'],
                    file.created_at.isoformat(),
                    file.expires_at.isoformat() if file.expires_at else 'Never'
                ])
            
            csv_data = output.getvalue()
            output.close()
            
            return jsonify({
                'csv_data': csv_data,
                'filename': f'sharesync_analytics_{datetime.utcnow().strftime("%Y%m%d")}.csv'
            })
        
    except Exception as e:
        return jsonify({'error': f'Analytics export failed: {str(e)}'}), 500

