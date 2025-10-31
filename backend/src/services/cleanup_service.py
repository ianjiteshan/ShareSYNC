import os
import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy import and_
import logging

from ..models.database import db
from ..models import File, Download, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self, app=None):
        self.app = app
        self.scheduler_thread = None
        self.is_running = False
        
    def init_app(self, app):
        """Initialize the cleanup service with Flask app"""
        self.app = app
        
    def start_scheduler(self):
        """Start the cleanup scheduler in a separate thread"""
        if self.is_running:
            logger.warning("Cleanup scheduler is already running")
            return
            
        self.is_running = True
        
        # Schedule cleanup tasks
        schedule.every(1).hours.do(self._cleanup_expired_files)
        schedule.every(6).hours.do(self._cleanup_orphaned_files)
        schedule.every(1).days.do(self._cleanup_old_downloads)
        schedule.every(1).days.do(self._cleanup_temp_files)
        schedule.every(7).days.do(self._generate_cleanup_report)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Cleanup scheduler started successfully")
        
    def stop_scheduler(self):
        """Stop the cleanup scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Cleanup scheduler stopped")
        
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)
                
    def _cleanup_expired_files(self):
        """Remove files that have passed their expiry date"""
        try:
            with self.app.app_context():
                current_time = datetime.utcnow()
                
                # Find expired files
                expired_files = File.query.filter(
                    and_(
                        File.expires_at <= current_time,
                        File.is_deleted == False
                    )
                ).all()
                
                cleanup_count = 0
                storage_freed = 0
                
                for file in expired_files:
                    try:
                        # Delete from storage (R2/local)
                        if self._delete_from_storage(file.storage_key):
                            storage_freed += file.file_size
                            
                        # Mark as deleted in database
                        file.is_deleted = True
                        file.deleted_at = current_time
                        cleanup_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to delete expired file {file.id}: {str(e)}")
                        
                db.session.commit()
                
                if cleanup_count > 0:
                    logger.info(f"Cleaned up {cleanup_count} expired files, freed {storage_freed / (1024*1024):.2f} MB")
                    
        except Exception as e:
            logger.error(f"Expired files cleanup failed: {str(e)}")
            
    def _cleanup_orphaned_files(self):
        """Remove files that exist in storage but not in database"""
        try:
            with self.app.app_context():
                # This would require listing all files in storage and comparing with database
                # For now, we'll implement a basic version
                
                # Find files marked as deleted but still in storage
                deleted_files = File.query.filter(
                    and_(
                        File.is_deleted == True,
                        File.deleted_at < datetime.utcnow() - timedelta(days=1)
                    )
                ).all()
                
                cleanup_count = 0
                for file in deleted_files:
                    try:
                        if self._delete_from_storage(file.storage_key):
                            cleanup_count += 1
                            # Remove from database completely
                            db.session.delete(file)
                    except Exception as e:
                        logger.error(f"Failed to cleanup orphaned file {file.id}: {str(e)}")
                        
                db.session.commit()
                
                if cleanup_count > 0:
                    logger.info(f"Cleaned up {cleanup_count} orphaned files")
                    
        except Exception as e:
            logger.error(f"Orphaned files cleanup failed: {str(e)}")
            
    def _cleanup_old_downloads(self):
        """Remove old download records to keep database clean"""
        try:
            with self.app.app_context():
                # Remove download records older than 90 days
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                
                old_downloads = Download.query.filter(
                    Download.created_at < cutoff_date
                ).all()
                
                cleanup_count = len(old_downloads)
                
                for download in old_downloads:
                    db.session.delete(download)
                    
                db.session.commit()
                
                if cleanup_count > 0:
                    logger.info(f"Cleaned up {cleanup_count} old download records")
                    
        except Exception as e:
            logger.error(f"Old downloads cleanup failed: {str(e)}")
            
    def _cleanup_temp_files(self):
        """Remove temporary files from the system"""
        try:
            temp_dirs = ['/tmp', '/var/tmp']
            cleanup_count = 0
            
            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue
                    
                # Remove files older than 24 hours
                cutoff_time = time.time() - (24 * 60 * 60)
                
                for filename in os.listdir(temp_dir):
                    if filename.startswith('sharesync_'):
                        filepath = os.path.join(temp_dir, filename)
                        try:
                            if os.path.getmtime(filepath) < cutoff_time:
                                os.remove(filepath)
                                cleanup_count += 1
                        except Exception as e:
                            logger.error(f"Failed to remove temp file {filepath}: {str(e)}")
                            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} temporary files")
                
        except Exception as e:
            logger.error(f"Temp files cleanup failed: {str(e)}")
            
    def _generate_cleanup_report(self):
        """Generate weekly cleanup report"""
        try:
            with self.app.app_context():
                week_ago = datetime.utcnow() - timedelta(days=7)
                
                # Count files cleaned up in the last week
                cleaned_files = File.query.filter(
                    and_(
                        File.is_deleted == True,
                        File.deleted_at >= week_ago
                    )
                ).count()
                
                # Calculate storage freed
                storage_freed = db.session.query(
                    db.func.sum(File.file_size)
                ).filter(
                    and_(
                        File.is_deleted == True,
                        File.deleted_at >= week_ago
                    )
                ).scalar() or 0
                
                # Active files count
                active_files = File.query.filter_by(is_deleted=False).count()
                
                # Total storage used
                total_storage = db.session.query(
                    db.func.sum(File.file_size)
                ).filter_by(is_deleted=False).scalar() or 0
                
                report = {
                    'period': '7 days',
                    'files_cleaned': cleaned_files,
                    'storage_freed_mb': round(storage_freed / (1024*1024), 2),
                    'active_files': active_files,
                    'total_storage_mb': round(total_storage / (1024*1024), 2),
                    'generated_at': datetime.utcnow().isoformat()
                }
                
                logger.info(f"Weekly cleanup report: {report}")
                
                # Store report in database or send to admin
                # For now, just log it
                
        except Exception as e:
            logger.error(f"Cleanup report generation failed: {str(e)}")
            
    def _delete_from_storage(self, storage_key):
        """Delete file from storage (R2 or local)"""
        try:
            # If using Cloudflare R2
            if os.getenv('USE_R2_STORAGE', 'false').lower() == 'true':
                return self._delete_from_r2(storage_key)
            else:
                return self._delete_from_local(storage_key)
        except Exception as e:
            logger.error(f"Storage deletion failed for {storage_key}: {str(e)}")
            return False
            
    def _delete_from_r2(self, storage_key):
        """Delete file from Cloudflare R2"""
        try:
            import boto3
            
            # Initialize R2 client
            r2_client = boto3.client(
                's3',
                endpoint_url=os.getenv('R2_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
                region_name='auto'
            )
            
            bucket_name = os.getenv('R2_BUCKET_NAME')
            
            # Delete object
            r2_client.delete_object(Bucket=bucket_name, Key=storage_key)
            return True
            
        except Exception as e:
            logger.error(f"R2 deletion failed: {str(e)}")
            return False
            
    def _delete_from_local(self, storage_key):
        """Delete file from local storage"""
        try:
            upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
            file_path = os.path.join(upload_folder, storage_key)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Local deletion failed: {str(e)}")
            return False
            
    def manual_cleanup(self, cleanup_type='all'):
        """Manually trigger cleanup operations"""
        try:
            with self.app.app_context():
                if cleanup_type in ['all', 'expired']:
                    self._cleanup_expired_files()
                    
                if cleanup_type in ['all', 'orphaned']:
                    self._cleanup_orphaned_files()
                    
                if cleanup_type in ['all', 'downloads']:
                    self._cleanup_old_downloads()
                    
                if cleanup_type in ['all', 'temp']:
                    self._cleanup_temp_files()
                    
                logger.info(f"Manual cleanup completed: {cleanup_type}")
                return True
                
        except Exception as e:
            logger.error(f"Manual cleanup failed: {str(e)}")
            return False
            
    def get_cleanup_stats(self):
        """Get cleanup statistics"""
        try:
            with self.app.app_context():
                # Files by status
                active_files = File.query.filter_by(is_deleted=False).count()
                deleted_files = File.query.filter_by(is_deleted=True).count()
                
                # Storage statistics
                active_storage = db.session.query(
                    db.func.sum(File.file_size)
                ).filter_by(is_deleted=False).scalar() or 0
                
                # Expired files count
                expired_files = File.query.filter(
                    and_(
                        File.expires_at <= datetime.utcnow(),
                        File.is_deleted == False
                    )
                ).count()
                
                # Files expiring soon (next 24 hours)
                expiring_soon = File.query.filter(
                    and_(
                        File.expires_at <= datetime.utcnow() + timedelta(hours=24),
                        File.expires_at > datetime.utcnow(),
                        File.is_deleted == False
                    )
                ).count()
                
                return {
                    'active_files': active_files,
                    'deleted_files': deleted_files,
                    'expired_files': expired_files,
                    'expiring_soon': expiring_soon,
                    'active_storage_mb': round(active_storage / (1024*1024), 2),
                    'scheduler_running': self.is_running,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Cleanup stats retrieval failed: {str(e)}")
            return None

# Global cleanup service instance
cleanup_service = CleanupService()

