from datetime import datetime
from .database import db

class User(db.Model):
    """User model for storing user information"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(255), primary_key=True)  # Google user ID
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    picture = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # User preferences
    upload_limit = db.Column(db.Integer, default=100)  # MB
    daily_upload_limit = db.Column(db.Integer, default=1000)  # MB per day
    is_premium = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    files = db.relationship('File', backref='user', lazy=True, cascade='all, delete-orphan')
    downloads = db.relationship('Download', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'upload_limit': self.upload_limit,
            'daily_upload_limit': self.daily_upload_limit,
            'is_premium': self.is_premium,
            'is_active': self.is_active
        }
    
    @classmethod
    def create_or_update(cls, user_data):
        """Create or update user from OAuth data"""
        user = cls.query.filter_by(id=user_data['id']).first()
        
        if user:
            # Update existing user
            user.email = user_data.get('email', user.email)
            user.name = user_data.get('name', user.name)
            user.picture = user_data.get('picture', user.picture)
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = cls(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data['name'],
                picture=user_data.get('picture'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
        
        db.session.commit()
        return user
    
    def get_upload_stats(self):
        """Get user upload statistics"""
        from .file import File
        from sqlalchemy import func
        
        today = datetime.utcnow().date()
        
        # Total files uploaded
        total_files = File.query.filter_by(user_id=self.id).count()
        
        # Total size uploaded
        total_size = db.session.query(func.sum(File.file_size)).filter_by(user_id=self.id).scalar() or 0
        
        # Files uploaded today
        files_today = File.query.filter(
            File.user_id == self.id,
            func.date(File.created_at) == today
        ).count()
        
        # Size uploaded today
        size_today = db.session.query(func.sum(File.file_size)).filter(
            File.user_id == self.id,
            func.date(File.created_at) == today
        ).scalar() or 0
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'files_today': files_today,
            'size_today': size_today,
            'size_today_mb': round(size_today / (1024 * 1024), 2),
            'remaining_daily_limit': max(0, self.daily_upload_limit - (size_today / (1024 * 1024)))
        }

