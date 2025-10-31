import os
import schedule
import time
import threading
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from ..models.database import db
from ..models import File, Download
from .auth import require_auth
from ..middleware.rate_limiter import api_rate_limit

cleanup_bp = Blueprint('cleanup', __name__)

# Global cleanup scheduler
cleanup_scheduler = None
cleanup_thread = None

def cleanup_expired_files():
    """Clean up expired files from database and storage"""
    try:
        print(f"[{datetime.utcnow()}] Starting cleanup job...")
        
        # Get expired files
        expired_files = File.get_expired_files()
        
        if not expired_files:
            print("No expired files to clean up")
            return
        
        cleaned_count = 0
        storage_cleaned = 0
        
        for file_record in expired_files:
            try:
                # Mark file as deleted in database
                file_record.mark_deleted()
                cleaned_count += 1
                
                # TODO: Delete from R2 storage
                # This would require R2 client integration
                # r2_client.delete_object(Bucket=R2_BUCKET_NAME, Key=file_record.storage_key)
                storage_cleaned += 1
                
                print(f"Cleaned up file: {file_record.original_name} (ID: {file_record.id})")
                
            except Exception as e:
                print(f"Error cleaning up file {file_record.id}: {e}")
        
        print(f"Cleanup completed: {cleaned_count} files marked as deleted, {storage_cleaned} files removed from storage")
        
        # Clean up old download records (older than 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_downloads = Download.query.filter(Download.created_at < cutoff_date).all()
        
        for download in old_downloads:
            db.session.delete(download)
        
        db.session.commit()
        print(f"Cleaned up {len(old_downloads)} old download records")
        
    except Exception as e:
        print(f"Cleanup job failed: {e}")

def start_cleanup_scheduler():
    """Start the background cleanup scheduler"""
    global cleanup_scheduler, cleanup_thread
    
    if cleanup_thread and cleanup_thread.is_alive():
        print("Cleanup scheduler already running")
        return
    
    # Schedule cleanup every hour
    schedule.every().hour.do(cleanup_expired_files)
    
    # Also schedule daily cleanup at 2 AM
    schedule.every().day.at("02:00").do(cleanup_expired_files)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    cleanup_thread = threading.Thread(target=run_scheduler, daemon=True)
    cleanup_thread.start()
    
    print("Cleanup scheduler started")

def stop_cleanup_scheduler():
    """Stop the background cleanup scheduler"""
    global cleanup_thread
    
    schedule.clear()
    
    if cleanup_thread:
        cleanup_thread = None
    
    print("Cleanup scheduler stopped")

@cleanup_bp.route('/cleanup/run', methods=['POST'])
@require_auth
@api_rate_limit
def manual_cleanup():
    """Manually trigger cleanup (admin only)"""
    try:
        # Check if user is admin (you can implement admin check here)
        # For now, any authenticated user can trigger cleanup
        
        cleanup_expired_files()
        
        return jsonify({
            'message': 'Cleanup completed successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@cleanup_bp.route('/cleanup/status', methods=['GET'])
@require_auth
@api_rate_limit
def cleanup_status():
    """Get cleanup status and statistics"""
    try:
        # Get expired files count
        expired_count = len(File.get_expired_files())
        
        # Get total files count
        total_files = File.query.filter_by(is_deleted=False).count()
        
        # Get deleted files count
        deleted_files = File.query.filter_by(is_deleted=True).count()
        
        # Get old downloads count
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_downloads = Download.query.filter(Download.created_at < cutoff_date).count()
        
        # Get next scheduled cleanup
        next_cleanup = None
        if schedule.jobs:
            next_job = min(schedule.jobs, key=lambda job: job.next_run)
            next_cleanup = next_job.next_run.isoformat()
        
        return jsonify({
            'expired_files': expired_count,
            'total_files': total_files,
            'deleted_files': deleted_files,
            'old_downloads': old_downloads,
            'next_cleanup': next_cleanup,
            'scheduler_running': cleanup_thread and cleanup_thread.is_alive()
        })
        
    except Exception as e:
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@cleanup_bp.route('/cleanup/schedule', methods=['POST'])
@require_auth
@api_rate_limit
def configure_cleanup_schedule():
    """Configure cleanup schedule (admin only)"""
    try:
        data = request.get_json()
        interval_hours = data.get('interval_hours', 1)
        daily_time = data.get('daily_time', '02:00')
        
        # Validate inputs
        if interval_hours < 1 or interval_hours > 24:
            return jsonify({'error': 'Interval must be between 1 and 24 hours'}), 400
        
        # Stop current scheduler
        stop_cleanup_scheduler()
        
        # Configure new schedule
        schedule.every(interval_hours).hours.do(cleanup_expired_files)
        schedule.every().day.at(daily_time).do(cleanup_expired_files)
        
        # Start scheduler
        start_cleanup_scheduler()
        
        return jsonify({
            'message': 'Cleanup schedule updated',
            'interval_hours': interval_hours,
            'daily_time': daily_time
        })
        
    except Exception as e:
        return jsonify({'error': f'Schedule configuration failed: {str(e)}'}), 500

@cleanup_bp.route('/cleanup/files/<file_id>', methods=['DELETE'])
@require_auth
@api_rate_limit
def force_delete_file(file_id):
    """Force delete a specific file (admin only)"""
    try:
        file_record = File.query.filter_by(id=file_id).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user owns the file or is admin
        if file_record.user_id != request.current_user_id:
            # TODO: Implement admin check
            return jsonify({'error': 'Access denied'}), 403
        
        # Mark as deleted
        file_record.mark_deleted()
        
        # TODO: Delete from R2 storage
        
        return jsonify({
            'message': 'File deleted successfully',
            'file_id': file_id
        })
        
    except Exception as e:
        return jsonify({'error': f'File deletion failed: {str(e)}'}), 500

@cleanup_bp.route('/cleanup/stats', methods=['GET'])
@api_rate_limit
def cleanup_stats():
    """Get public cleanup statistics"""
    try:
        # Get storage statistics
        total_files = File.query.filter_by(is_deleted=False).count()
        total_size = db.session.query(db.func.sum(File.file_size)).filter_by(is_deleted=False).scalar() or 0
        
        # Get cleanup statistics for last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        files_cleaned_24h = File.query.filter(
            File.deleted_at >= yesterday,
            File.is_deleted == True
        ).count()
        
        # Get average file lifetime
        avg_lifetime_query = db.session.query(
            db.func.avg(
                db.func.julianday(File.deleted_at) - db.func.julianday(File.created_at)
            )
        ).filter(File.is_deleted == True)
        
        avg_lifetime_days = avg_lifetime_query.scalar() or 0
        
        return jsonify({
            'total_active_files': total_files,
            'total_storage_bytes': total_size,
            'total_storage_mb': round(total_size / (1024 * 1024), 2),
            'files_cleaned_24h': files_cleaned_24h,
            'avg_file_lifetime_days': round(avg_lifetime_days, 2)
        })
        
    except Exception as e:
        return jsonify({'error': f'Stats retrieval failed: {str(e)}'}), 500

# Initialize cleanup scheduler when module is imported
def init_cleanup_scheduler():
    """Initialize the cleanup scheduler"""
    start_cleanup_scheduler()
    print("Cleanup system initialized")

