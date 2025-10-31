from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

from ..models.database import db
from ..models import File, Download, User
from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit

dashboard_bp = Blueprint('dashboard', __name__)

def get_date_range(period='7d'):
    """Get date range based on period"""
    now = datetime.utcnow()
    
    if period == '24h':
        start_date = now - timedelta(hours=24)
    elif period == '7d':
        start_date = now - timedelta(days=7)
    elif period == '30d':
        start_date = now - timedelta(days=30)
    elif period == '90d':
        start_date = now - timedelta(days=90)
    elif period == '1y':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=7)
    
    return start_date, now

@dashboard_bp.route('/dashboard/overview', methods=['GET'])
@require_auth
@api_rate_limit
def get_dashboard_overview():
    """Get comprehensive dashboard overview for authenticated user"""
    try:
        user_id = request.current_user_id
        period = request.args.get('period', '7d')
        start_date, end_date = get_date_range(period)
        
        # User's file statistics
        user_files = File.query.filter_by(user_id=user_id, is_deleted=False)
        total_files = user_files.count()
        
        # Total storage used
        total_storage = db.session.query(func.sum(File.file_size)).filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).scalar() or 0
        
        # Files uploaded in period
        files_in_period = File.query.filter(
            File.user_id == user_id,
            File.created_at >= start_date,
            File.created_at <= end_date,
            File.is_deleted == False
        ).count()
        
        # Total downloads across all user's files
        total_downloads = db.session.query(func.sum(File.download_count)).filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).scalar() or 0
        
        # Downloads in period
        downloads_in_period = Download.query.join(File).filter(
            File.user_id == user_id,
            Download.created_at >= start_date,
            Download.created_at <= end_date
        ).count()
        
        # Most popular files
        popular_files = db.session.query(File).filter(
            File.user_id == user_id,
            File.is_deleted == False,
            File.download_count > 0
        ).order_by(File.download_count.desc()).limit(5).all()
        
        # Recent activity
        recent_files = File.query.filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).order_by(File.created_at.desc()).limit(10).all()
        
        # File type distribution
        file_types = db.session.query(
            func.substr(File.mime_type, 1, func.instr(File.mime_type, '/') - 1).label('type'),
            func.count().label('count')
        ).filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).group_by('type').all()
        
        return jsonify({
            'overview': {
                'total_files': total_files,
                'total_storage_bytes': total_storage,
                'total_storage_mb': round(total_storage / (1024 * 1024), 2),
                'total_downloads': total_downloads,
                'files_uploaded_period': files_in_period,
                'downloads_period': downloads_in_period,
                'period': period
            },
            'popular_files': [{
                'id': f.id,
                'name': f.original_name,
                'downloads': f.download_count,
                'size': f.file_size,
                'created_at': f.created_at.isoformat()
            } for f in popular_files],
            'recent_files': [{
                'id': f.id,
                'name': f.original_name,
                'size': f.file_size,
                'downloads': f.download_count,
                'created_at': f.created_at.isoformat(),
                'expires_at': f.expires_at.isoformat() if f.expires_at else None
            } for f in recent_files],
            'file_types': [{
                'type': ft.type or 'unknown',
                'count': ft.count
            } for ft in file_types]
        })
        
    except Exception as e:
        return jsonify({'error': f'Dashboard overview failed: {str(e)}'}), 500

@dashboard_bp.route('/dashboard/charts/uploads', methods=['GET'])
@require_auth
@api_rate_limit
def get_upload_chart_data():
    """Get upload chart data for time series visualization"""
    try:
        user_id = request.current_user_id
        period = request.args.get('period', '7d')
        start_date, end_date = get_date_range(period)
        
        # Determine grouping based on period
        if period == '24h':
            # Group by hour
            date_format = '%Y-%m-%d %H:00:00'
            interval = timedelta(hours=1)
        elif period in ['7d', '30d']:
            # Group by day
            date_format = '%Y-%m-%d'
            interval = timedelta(days=1)
        else:
            # Group by week
            date_format = '%Y-%W'
            interval = timedelta(weeks=1)
        
        # Get upload data grouped by time
        uploads = db.session.query(
            func.strftime(date_format, File.created_at).label('period'),
            func.count().label('count'),
            func.sum(File.file_size).label('total_size')
        ).filter(
            File.user_id == user_id,
            File.created_at >= start_date,
            File.created_at <= end_date,
            File.is_deleted == False
        ).group_by('period').order_by('period').all()
        
        # Get download data grouped by time
        downloads = db.session.query(
            func.strftime(date_format, Download.created_at).label('period'),
            func.count().label('count')
        ).join(File).filter(
            File.user_id == user_id,
            Download.created_at >= start_date,
            Download.created_at <= end_date
        ).group_by('period').order_by('period').all()
        
        # Create complete time series
        current = start_date
        chart_data = []
        
        upload_dict = {u.period: {'count': u.count, 'size': u.total_size} for u in uploads}
        download_dict = {d.period: d.count for d in downloads}
        
        while current <= end_date:
            if period == '24h':
                period_key = current.strftime('%Y-%m-%d %H:00:00')
                label = current.strftime('%H:00')
            elif period in ['7d', '30d']:
                period_key = current.strftime('%Y-%m-%d')
                label = current.strftime('%m/%d')
            else:
                period_key = current.strftime('%Y-%W')
                label = f"Week {current.strftime('%W')}"
            
            upload_data = upload_dict.get(period_key, {'count': 0, 'size': 0})
            download_count = download_dict.get(period_key, 0)
            
            chart_data.append({
                'period': period_key,
                'label': label,
                'uploads': upload_data['count'],
                'downloads': download_count,
                'storage_mb': round((upload_data['size'] or 0) / (1024 * 1024), 2)
            })
            
            current += interval
        
        return jsonify({
            'chart_data': chart_data,
            'period': period,
            'total_points': len(chart_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Chart data retrieval failed: {str(e)}'}), 500

@dashboard_bp.route('/dashboard/analytics/detailed', methods=['GET'])
@require_auth
@api_rate_limit
def get_detailed_analytics():
    """Get detailed analytics for power users"""
    try:
        user_id = request.current_user_id
        period = request.args.get('period', '30d')
        start_date, end_date = get_date_range(period)
        
        # File size distribution
        size_ranges = [
            (0, 1024*1024, '< 1MB'),
            (1024*1024, 10*1024*1024, '1-10MB'),
            (10*1024*1024, 100*1024*1024, '10-100MB'),
            (100*1024*1024, float('inf'), '> 100MB')
        ]
        
        size_distribution = []
        for min_size, max_size, label in size_ranges:
            if max_size == float('inf'):
                count = File.query.filter(
                    File.user_id == user_id,
                    File.file_size >= min_size,
                    File.is_deleted == False
                ).count()
            else:
                count = File.query.filter(
                    File.user_id == user_id,
                    File.file_size >= min_size,
                    File.file_size < max_size,
                    File.is_deleted == False
                ).count()
            
            size_distribution.append({
                'range': label,
                'count': count
            })
        
        # Download patterns by hour
        hourly_downloads = db.session.query(
            func.strftime('%H', Download.created_at).label('hour'),
            func.count().label('count')
        ).join(File).filter(
            File.user_id == user_id,
            Download.created_at >= start_date,
            Download.created_at <= end_date
        ).group_by('hour').order_by('hour').all()
        
        # Top referrers (if we track them)
        # For now, we'll simulate this data
        top_referrers = [
            {'source': 'Direct', 'count': 45},
            {'source': 'Email', 'count': 23},
            {'source': 'Social Media', 'count': 12},
            {'source': 'QR Code', 'count': 8}
        ]
        
        # Geographic distribution (simulated)
        geographic_data = [
            {'country': 'United States', 'downloads': 34},
            {'country': 'United Kingdom', 'downloads': 18},
            {'country': 'Germany', 'downloads': 12},
            {'country': 'Canada', 'downloads': 9},
            {'country': 'Australia', 'downloads': 7}
        ]
        
        # File expiry analysis
        expiry_analysis = db.session.query(
            func.case([
                (File.expires_at.is_(None), 'Never'),
                (File.expires_at > datetime.utcnow(), 'Active'),
                (File.expires_at <= datetime.utcnow(), 'Expired')
            ]).label('status'),
            func.count().label('count')
        ).filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).group_by('status').all()
        
        return jsonify({
            'size_distribution': size_distribution,
            'hourly_downloads': [{
                'hour': int(hd.hour),
                'count': hd.count
            } for hd in hourly_downloads],
            'top_referrers': top_referrers,
            'geographic_data': geographic_data,
            'expiry_analysis': [{
                'status': ea.status,
                'count': ea.count
            } for ea in expiry_analysis],
            'period': period
        })
        
    except Exception as e:
        return jsonify({'error': f'Detailed analytics failed: {str(e)}'}), 500

@dashboard_bp.route('/dashboard/export', methods=['POST'])
@require_auth
@api_rate_limit
def export_analytics_data():
    """Export analytics data in various formats"""
    try:
        user_id = request.current_user_id
        data = request.get_json()
        export_format = data.get('format', 'json')  # json, csv
        period = data.get('period', '30d')
        
        start_date, end_date = get_date_range(period)
        
        # Get all user's files with analytics
        files_data = db.session.query(File).filter(
            File.user_id == user_id,
            File.created_at >= start_date,
            File.created_at <= end_date,
            File.is_deleted == False
        ).all()
        
        export_data = []
        for file in files_data:
            export_data.append({
                'file_id': file.id,
                'filename': file.original_name,
                'size_bytes': file.file_size,
                'mime_type': file.mime_type,
                'upload_date': file.created_at.isoformat(),
                'expiry_date': file.expires_at.isoformat() if file.expires_at else None,
                'download_count': file.download_count,
                'is_password_protected': file.is_password_protected,
                'storage_key': file.storage_key
            })
        
        if export_format == 'csv':
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys() if export_data else [])
            writer.writeheader()
            writer.writerows(export_data)
            
            return jsonify({
                'format': 'csv',
                'data': output.getvalue(),
                'filename': f'sharesync_analytics_{period}_{datetime.utcnow().strftime("%Y%m%d")}.csv'
            })
        
        # Default JSON format
        return jsonify({
            'format': 'json',
            'data': export_data,
            'metadata': {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_files': len(export_data),
                'export_date': datetime.utcnow().isoformat()
            },
            'filename': f'sharesync_analytics_{period}_{datetime.utcnow().strftime("%Y%m%d")}.json'
        })
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@dashboard_bp.route('/dashboard/realtime', methods=['GET'])
@require_auth
@api_rate_limit
def get_realtime_stats():
    """Get real-time statistics for live dashboard updates"""
    try:
        user_id = request.current_user_id
        
        # Last 24 hours activity
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        # Recent uploads
        recent_uploads = File.query.filter(
            File.user_id == user_id,
            File.created_at >= last_24h,
            File.is_deleted == False
        ).count()
        
        # Recent downloads
        recent_downloads = Download.query.join(File).filter(
            File.user_id == user_id,
            Download.created_at >= last_24h
        ).count()
        
        # Active files (not expired)
        active_files = File.query.filter(
            File.user_id == user_id,
            File.is_deleted == False,
            or_(File.expires_at.is_(None), File.expires_at > datetime.utcnow())
        ).count()
        
        # Storage usage
        current_storage = db.session.query(func.sum(File.file_size)).filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).scalar() or 0
        
        # Latest activity (last 10 actions)
        latest_files = File.query.filter(
            File.user_id == user_id,
            File.is_deleted == False
        ).order_by(File.created_at.desc()).limit(5).all()
        
        latest_downloads = Download.query.join(File).filter(
            File.user_id == user_id
        ).order_by(Download.created_at.desc()).limit(5).all()
        
        return jsonify({
            'stats': {
                'uploads_24h': recent_uploads,
                'downloads_24h': recent_downloads,
                'active_files': active_files,
                'storage_mb': round(current_storage / (1024 * 1024), 2),
                'timestamp': datetime.utcnow().isoformat()
            },
            'latest_activity': {
                'uploads': [{
                    'id': f.id,
                    'name': f.original_name,
                    'size': f.file_size,
                    'created_at': f.created_at.isoformat()
                } for f in latest_files],
                'downloads': [{
                    'file_id': d.file_id,
                    'file_name': d.file.original_name,
                    'downloaded_at': d.created_at.isoformat(),
                    'ip_address': d.ip_address
                } for d in latest_downloads]
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Real-time stats failed: {str(e)}'}), 500

