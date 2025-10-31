from datetime import datetime
from .database import db

class Download(db.Model):
    """Download model for tracking file downloads"""
    
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(36), db.ForeignKey('files.id'), nullable=False)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=True)  # Nullable for anonymous downloads
    
    # Download information
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    referer = db.Column(db.String(500), nullable=True)
    
    # Geographic information (optional)
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # Download status
    download_status = db.Column(db.String(20), default='initiated')  # initiated, completed, failed
    bytes_downloaded = db.Column(db.BigInteger, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Download {self.file_id} by {self.user_id or "Anonymous"}>'
    
    def to_dict(self):
        """Convert download to dictionary"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'country': self.country,
            'city': self.city,
            'download_status': self.download_status,
            'bytes_downloaded': self.bytes_downloaded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def create_download_record(cls, file_id, user_id=None, request_data=None):
        """Create a new download record"""
        download = cls(
            file_id=file_id,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        
        # Add request information if available
        if request_data:
            download.ip_address = request_data.get('ip_address')
            download.user_agent = request_data.get('user_agent')
            download.referer = request_data.get('referer')
        
        db.session.add(download)
        db.session.commit()
        return download
    
    def mark_completed(self, bytes_downloaded=None):
        """Mark download as completed"""
        self.download_status = 'completed'
        self.completed_at = datetime.utcnow()
        if bytes_downloaded:
            self.bytes_downloaded = bytes_downloaded
        db.session.commit()
    
    def mark_failed(self):
        """Mark download as failed"""
        self.download_status = 'failed'
        db.session.commit()
    
    @classmethod
    def get_file_download_stats(cls, file_id):
        """Get download statistics for a file"""
        from sqlalchemy import func
        
        stats = db.session.query(
            func.count(cls.id).label('total_downloads'),
            func.count(cls.id).filter(cls.download_status == 'completed').label('completed_downloads'),
            func.sum(cls.bytes_downloaded).label('total_bytes'),
            func.count(func.distinct(cls.ip_address)).label('unique_ips'),
            func.count(func.distinct(cls.user_id)).label('unique_users')
        ).filter(cls.file_id == file_id).first()
        
        return {
            'total_downloads': stats.total_downloads or 0,
            'completed_downloads': stats.completed_downloads or 0,
            'total_bytes': stats.total_bytes or 0,
            'unique_ips': stats.unique_ips or 0,
            'unique_users': stats.unique_users or 0
        }
    
    @classmethod
    def get_user_download_history(cls, user_id, limit=50):
        """Get download history for a user"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit)\
                      .all()
    
    @classmethod
    def get_popular_files(cls, limit=10, days=7):
        """Get most downloaded files in the last N days"""
        from sqlalchemy import func
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            cls.file_id,
            func.count(cls.id).label('download_count')
        ).filter(
            cls.created_at >= cutoff_date,
            cls.download_status == 'completed'
        ).group_by(cls.file_id)\
         .order_by(func.count(cls.id).desc())\
         .limit(limit)\
         .all()

