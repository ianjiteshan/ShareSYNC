# ShareSync - Ultimate File Sharing Platform

## Complete Deployment Guide

ShareSync is a superior file sharing platform that combines the best features of local and cloud file sharinng with enhanced capabilities, modern design, and enterprise-grade security.

## 🚀 Features Overview

### ✅ **Core Features Implemented**
- **Dual Sharing Modes**: P2P local sharing + Cloud storage via Cloudflare R2
- **Modern UI**: Zapdrop-inspired design with enhanced UX
- **Authentication**: Google OAuth integration
- **Security**: Advanced file scanning, malware detection, password protection
- **Analytics**: Comprehensive dashboard with usage statistics
- **File Management**: Automated cleanup, expiry settings, size limits
- **QR Code Sharing**: Instant QR code generation for easy sharing
- **Progress Tracking**: Real-time upload/download progress with speed indicators
- **Legal Compliance**: Terms of Service and Privacy Policy pages

### 🔧 **Technical Stack**
- **Frontend**: React + Vite + TailwindCSS + Framer Motion
- **Backend**: Flask + SQLAlchemy + SocketIO + APScheduler
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **Storage**: Cloudflare R2 (with local fallback)
- **Authentication**: Google OAuth 2.0
- **Security**: File scanning, rate limiting, encryption

## 📦 **Project Structure**

```
ShareSync-Ultimate-Complete-Project/
├──frontend/                 # React Frontend
│   ├── src/
│   │   ├── components/                  # UI Components
│   │   │   ├── HomePage.jsx            # Landing page
│   │   │   ├── UploadPage.jsx          # Cloud upload interface
│   │   │   ├── P2PPage.jsx             # P2P sharing interface
│   │   │   ├── AnalyticsDashboard.jsx  # Analytics dashboard
│   │   │   ├── QRCodeGenerator.jsx     # QR code components
│   │   │   ├── FilePreview.jsx         # File preview system
│   │   │   ├── ProgressTracker.jsx     # Progress tracking
│   │   │   ├── TermsOfService.jsx      # Legal pages
│   │   │   ├── PrivacyPolicy.jsx       # Privacy policy
│   │   │   └── Footer.jsx              # Site footer
│   │   ├── hooks/                      # React hooks
│   │   └── lib/                        # Utilities
│   ├── dist/                           # Built frontend (production ready)
│   └── package.json                    # Dependencies
│
├── backend/         # Flask Backend
│   ├── src/
│   │   ├── routes/                     # API Routes
│   │   │   ├── auth.py                 # Authentication
│   │   │   ├── upload.py               # File upload/download
│   │   │   ├── p2p.py                  # P2P signaling
│   │   │   ├── files.py                # File management
│   │   │   ├── analytics.py            # Usage analytics
│   │   │   ├── dashboard.py            # Dashboard data
│   │   │   ├── password.py             # Password protection
│   │   │   ├── limits.py               # Usage limits
│   │   │   ├── cleanup.py              # File cleanup
│   │   │   └── security.py             # Security features
│   │   ├── models/                     # Database models
│   │   ├── services/                   # Background services
│   │   ├── middleware/                 # Rate limiting, etc.
│   │   ├── static/                     # Frontend files
│   │   └── main.py                     # Application entry point
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Environment variables template
│
└── Documentation/                      # Research and analysis
    ├── research_notes.md               # Technical research
    ├── pairdrop_features_analysis.md   # PairDrop analysis
    └── zapdrop_features_analysis.md    # Zapdrop analysis
```

## 🛠 **Installation & Setup**

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Project Unzipping
```bash
tar -xzf ShareSync-Ultimate-Complete-Project.tar
cd ShareSync-Ultimate-Complete-Project
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Environment Configuration
Edit `.env` file with your settings:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
PORT=5000

# Database
DATABASE_URL=sqlite:///sharesync.db

# Google OAuth (Required)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Cloudflare R2 (Optional - will use local storage if not configured)
USE_R2_STORAGE=true
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret-key
R2_BUCKET_NAME=your-bucket-name

# Security
RATE_LIMIT_STORAGE_URL=memory://
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=104857600  # 100MB
```

### 4. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:5000/api/auth/callback` (development)
   - `https://yourdomain.com/api/auth/callback` (production)

### 5. Cloudflare R2 Setup (Optional)
1. Sign up for Cloudflare
2. Create R2 bucket
3. Generate API tokens with R2 permissions
4. Configure CORS for your bucket

### 6. Run the Application
```bash
# Start backend
cd enhanced-file-share-backend
source venv/bin/activate
python src/main.py

# Application will be available at http://localhost:5000
```

## 🚀 **Production Deployment**

### Using Docker (Recommended)
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY enhanced-file-share-backend/ .

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "src/main.py"]
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

### Environment Variables for Production
```env
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
USE_R2_STORAGE=true
# ... other production settings
```

## 🔧 **API Documentation**

### Authentication Endpoints
- `GET /api/auth/login` - Initiate Google OAuth
- `GET /api/auth/callback` - OAuth callback
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/user` - Get current user info

### File Management
- `POST /api/upload/presigned-url` - Get upload URL
- `POST /api/upload/complete` - Complete upload
- `GET /api/files/<id>/download` - Download file
- `DELETE /api/files/<id>` - Delete file
- `POST /api/files/<id>/password` - Set password protection

### Analytics & Dashboard
- `GET /api/dashboard/overview` - Dashboard overview
- `GET /api/dashboard/charts/uploads` - Upload charts
- `GET /api/analytics/stats` - Usage statistics

### Security Features
- `POST /api/security/scan-file` - Scan file for threats
- `GET /api/security/file-preview/<id>` - Secure file preview
- `POST /api/security/quarantine/<id>` - Quarantine file

### P2P Signaling (WebSocket)
- `connect` - Join P2P network
- `offer` - Send WebRTC offer
- `answer` - Send WebRTC answer
- `ice-candidate` - Exchange ICE candidates

## 🛡 **Security Features**

### File Security
- **Malware Scanning**: Automatic file scanning for threats
- **File Type Validation**: Whitelist of allowed file types
- **Size Limits**: Configurable file size restrictions
- **Password Protection**: Optional password protection for files
- **Encryption**: Files encrypted in transit and at rest

### Access Control
- **Authentication**: Google OAuth required for uploads
- **Rate Limiting**: API rate limiting to prevent abuse
- **Session Management**: Secure session handling
- **CORS Protection**: Proper CORS configuration

### Privacy
- **Auto-Expiry**: Files automatically deleted after expiry
- **No Permanent Storage**: Temporary file storage only
- **Minimal Data Collection**: Only necessary data collected
- **GDPR Compliance**: Privacy-focused design

## 📊 **Monitoring & Analytics**

### Built-in Analytics
- Upload/download statistics
- File type distribution
- User activity tracking
- Storage usage monitoring
- Performance metrics

### Cleanup & Maintenance
- Automated file cleanup (hourly)
- Orphaned file detection
- Database optimization
- Log rotation
- Health checks

## 🔄 **Backup & Recovery**

### Database Backup
```bash
# SQLite backup
cp src/database/sharesync.db backup/sharesync_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump $DATABASE_URL > backup/sharesync_$(date +%Y%m%d).sql
```

### File Storage Backup
- Cloudflare R2 provides automatic redundancy
- Local storage should be backed up regularly
- Consider implementing automated backup scripts

## 🐛 **Troubleshooting**

### Common Issues

1. **Google OAuth not working**
   - Check client ID and secret
   - Verify redirect URIs
   - Ensure Google+ API is enabled

2. **File uploads failing**
   - Check file size limits
   - Verify R2 credentials
   - Check network connectivity

3. **P2P not connecting**
   - Check firewall settings
   - Verify WebSocket connection
   - Test on same network first

### Logs
- Application logs: Check console output
- Error logs: `logs/error.log`
- Access logs: `logs/access.log`

## 📈 **Performance Optimization**

### Frontend
- Built with Vite for optimal bundling
- Code splitting implemented
- Image optimization
- Lazy loading for components

### Backend
- Database indexing
- Connection pooling
- Caching strategies
- Background job processing

### Infrastructure
- CDN for static assets
- Load balancing for high traffic
- Database replication
- Monitoring and alerting

## 🔮 **Future Enhancements**

### Planned Features
- Mobile app (React Native)
- Advanced file versioning
- Team collaboration features
- API rate limiting tiers
- Enterprise SSO integration
- Advanced analytics dashboard
- File synchronization
- Bulk operations

### Scalability
- Microservices architecture
- Kubernetes deployment
- Database sharding
- Redis caching
- Message queues

## 📞 **Support**

### Documentation
- API documentation: `/api/docs`
- User guide: Available in app
- Developer docs: This file

### Community
- GitHub Issues: Report bugs
- Discussions: Feature requests
- Wiki: Community documentation

## 📄 **License**

ShareSync is released under the MIT License. See LICENSE file for details.

---

**ShareSync** - The Ultimate File Sharing Platform
Built with ❤️ by Anjitesh Shandilya

*Inspiration-PairDrop and Zapdrop*

