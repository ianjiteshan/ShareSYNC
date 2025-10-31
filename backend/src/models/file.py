from datetime import datetime, timedelta
from .database import db
import uuid
import hashlib

class File(db.Model):
    """File model for storing file metadata"""
    
    __tablename__ = 'files'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    
    # File information
    original_name = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)  # Size in bytes
    file_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash
    
    # Storage information
    storage_key = db.Column(db.String(500), nullable=False)  # R2 object key
    storage_url = db.Column(db.String(1000), nullable=True)  # Public URL if available
    
    # Access control
    is_public = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(255), nullable=True)  # For password protection
    download_limit = db.Column(db.Integer, nullable=True)  # Max downloads allowed
    download_count = db.Column(db.Integer, default=0)  # Current download count
    
    # Expiry settings
    expires_at = db.Column(db.DateTime, nullable=False)
    auto_delete = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Status
    upload_status = db.Column(db.String(20), default='pending')  # pending, uploading, completed, failed
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Relationships
    downloads = db.relationship('Download', backref='file', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<File {self.original_name}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert file to dictionary"""
        data = {
            'id': self.id,
            'original_name': self.original_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'is_public': self.is_public,
            'has_password': bool(self.password_hash),
            'download_limit': self.download_limit,
            'download_count': self.download_count,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'upload_status': self.upload_status,
            'is_deleted': self.is_deleted,
            'is_expired': self.is_expired(),
            'can_download': self.can_download()
        }
        
        if include_sensitive:
            data.update({
                'user_id': self.user_id,
                'storage_key': self.storage_key,
                'storage_url': self.storage_url,
                'file_hash': self.file_hash
            })
        
        return data
    
    def is_expired(self):
        """Check if file has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def can_download(self):
        """Check if file can be downloaded"""
        if self.is_deleted or self.is_expired():
            return False
        
        if self.upload_status != 'completed':
            return False
        
        if self.download_limit and self.download_count >= self.download_limit:
            return False
        
        return True
    
    def set_password(self, password):
        """Set password protection for file"""
        if password:
            self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        else:
            self.password_hash = None
    
    def check_password(self, password):
        """Check if provided password is correct"""
        if not self.password_hash:
            return True  # No password protection
        
        if not password:
            return False
        
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def increment_download_count(self):
        """Increment download counter"""
        self.download_count += 1
        db.session.commit()
    
    def mark_deleted(self):
        """Mark file as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_file(cls, user_id, file_data, expiry_hours=24):
        """Create a new file record"""
        file_record = cls(
            user_id=user_id,
            original_name=file_data['original_name'],
            file_type=file_data['file_type'],
            file_size=file_data['file_size'],
            storage_key=file_data['storage_key'],
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Set optional fields
        if 'password' in file_data:
            file_record.set_password(file_data['password'])
        
        if 'download_limit' in file_data:
            file_record.download_limit = file_data['download_limit']
        
        if 'is_public' in file_data:
            file_record.is_public = file_data['is_public']
        
        db.session.add(file_record)
        db.session.commit()
        return file_record
    
    @classmethod
    def get_expired_files(cls):
        """Get all expired files that should be deleted"""
        return cls.query.filter(
            cls.expires_at < datetime.utcnow(),
            cls.auto_delete == True,
            cls.is_deleted == False
        ).all()
    
    @classmethod
    def cleanup_expired_files(cls):
        """Mark expired files as deleted"""
        expired_files = cls.get_expired_files()
        count = 0
        
        for file in expired_files:
            file.mark_deleted()
            count += 1
        
        return count
    
    def get_share_url(self, base_url):
        """Generate shareable URL for file"""
        return f"{base_url}/files/{self.id}"
    
    def get_file_icon(self):
        """Get appropriate icon for file type"""
        file_type_icons = {
            'image': '🖼️',
            'video': '🎥',
            'audio': '🎵',
            'document': '📄',
            'pdf': '📕',
            'archive': '📦',
            'code': '💻',
            'text': '📝'
        }
        
        # Determine file category from MIME type
        if self.file_type.startswith('image/'):
            return file_type_icons.get('image', '📄')
        elif self.file_type.startswith('video/'):
            return file_type_icons.get('video', '📄')
        elif self.file_type.startswith('audio/'):
            return file_type_icons.get('audio', '📄')
        elif 'pdf' in self.file_type:
            return file_type_icons.get('pdf', '📄')
        elif any(ext in self.file_type for ext in ['zip', 'rar', 'tar', 'gz']):
            return file_type_icons.get('archive', '📄')
        elif any(ext in self.file_type for ext in ['javascript', 'python', 'html', 'css']):
            return file_type_icons.get('code', '📄')
        elif self.file_type.startswith('text/'):
            return file_type_icons.get('text', '📄')
        else:
            return file_type_icons.get('document', '📄')

