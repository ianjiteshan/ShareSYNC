# ShareSync - Enhanced File Sharing

ShareSync is a modern file sharing application that combines the best features of PairDrop (P2P sharing) and Zapdrop (cloud storage) with a superior visual design, Google Authentication, and advanced rate limiting.

## Features

- **P2P File Sharing**: Direct device-to-device file sharing using WebRTC
- **Cloud Storage**: Upload files to Cloudflare R2 with expiring links
- **Google Authentication**: Secure sign-in with Google OAuth 2.0
- **Advanced Rate Limiting**: User-based and IP-based rate limits with Redis support
- **Modern UI**: Beautiful, responsive interface inspired by Zapdrop
- **Real-time Communication**: WebSocket-based signaling for P2P connections
- **Secure**: End-to-end encryption for P2P, secure cloud storage with presigned URLs

## Architecture

- **Frontend**: React + Vite + TailwindCSS + Framer Motion
- **Backend**: Flask + SocketIO + SQLAlchemy + OAuth
- **Authentication**: Google OAuth 2.0 with session management
- **Rate Limiting**: Advanced multi-tier rate limiting (IP + User based)
- **Storage**: Cloudflare R2 (S3-compatible)
- **P2P**: WebRTC with WebSocket signaling
- **Caching**: Redis (optional, falls back to memory)

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- Cloudflare R2 account (for cloud storage)
- Google Cloud Console project (for OAuth)
- Redis (optional, for production rate limiting)

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:5000/api/auth/callback` (development)
   - `https://yourdomain.com/api/auth/callback` (production)
7. Copy Client ID and Client Secret

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd enhanced-file-share-backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # - Cloudflare R2 credentials
   # - Google OAuth credentials
   # - Redis URL (optional)
   ```

5. Run the backend:
   ```bash
   python src/main.py
   ```

The backend will run on `http://localhost:5000`

### Frontend Setup (Development)

1. Navigate to the frontend directory:
   ```bash
   cd enhanced-file-share
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run development server:
   ```bash
   npm run dev
   ```

The frontend will run on `http://localhost:5173`

### Production Deployment

The backend serves the built frontend from the `static` folder. To deploy:

1. Build the frontend:
   ```bash
   cd enhanced-file-share
   npm run build
   ```

2. Copy built files to backend:
   ```bash
   cp -r dist/* ../enhanced-file-share-backend/src/static/
   ```

3. Run the backend:
   ```bash
   cd enhanced-file-share-backend
   source venv/bin/activate
   python src/main.py
   ```

## Configuration

### Environment Variables

```bash
# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_BUCKET_NAME=sharesync-files

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Redis Configuration (for production rate limiting)
REDIS_URL=redis://localhost:6379
```

### Rate Limiting Configuration

The application includes advanced rate limiting with different tiers:

- **Upload Endpoints**: 50/hour per IP, 200/hour per user, 5/hour anonymous
- **Download Endpoints**: 200/hour per IP, 1000/hour per user, 50/hour anonymous
- **API Endpoints**: 1000/hour per IP, 5000/hour per user, 100/hour anonymous
- **Auth Endpoints**: 10/10min per IP, 50/10min per user, 2/10min anonymous

## API Endpoints

### Authentication Endpoints
- `GET /api/auth/login` - Initiate Google OAuth login
- `GET /api/auth/callback` - Handle OAuth callback
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/user` - Get current user info
- `GET /api/auth/status` - Check auth status

### Upload Endpoints
- `POST /api/upload/presigned-url` - Get presigned URL for file upload (requires auth)
- `POST /api/upload/complete` - Mark upload as complete (requires auth)
- `GET /api/upload/download/<file_id>` - Get download URL
- `GET /api/upload/info/<file_id>` - Get file information

### P2P Endpoints
- `GET /api/p2p/status` - Get P2P status
- `POST /api/p2p/generate-room` - Generate new room ID

### WebSocket Events
- `connect` - Client connects to signaling server
- `join_room` - Join a P2P room
- `webrtc_offer` - Send WebRTC offer
- `webrtc_answer` - Send WebRTC answer
- `webrtc_ice_candidate` - Send ICE candidate

## Authentication Flow

1. User clicks "Sign in with Google"
2. Redirected to Google OAuth consent screen
3. After consent, redirected back to `/api/auth/callback`
4. Backend exchanges code for user info
5. User session created and stored
6. User redirected to `/upload` page
7. Protected routes check authentication status

## Rate Limiting Features

- **Multi-tier limits**: Different limits for authenticated vs anonymous users
- **IP-based protection**: Prevents abuse from single IP addresses
- **User-based quotas**: Higher limits for authenticated users
- **Redis support**: Scalable rate limiting with Redis backend
- **Memory fallback**: Works without Redis for development
- **Sliding window**: More accurate rate limiting algorithm

## File Structure

```
enhanced-file-share-backend/
├── src/
│   ├── middleware/       # Rate limiting middleware
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   │   ├── auth.py      # Authentication routes
│   │   ├── upload.py    # Cloud upload routes
│   │   ├── p2p.py       # P2P signaling routes
│   │   └── user.py      # User routes
│   ├── static/          # Built frontend files
│   └── main.py          # Flask application entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file

enhanced-file-share/
├── src/
│   ├── components/      # React components
│   │   ├── HomePage.jsx
│   │   ├── UploadPage.jsx
│   │   ├── P2PPage.jsx
│   │   ├── AuthPage.jsx
│   │   └── ProtectedRoute.jsx
│   ├── hooks/          # React hooks
│   │   └── useAuth.jsx # Authentication hook
│   ├── lib/            # Utilities
│   └── App.jsx         # Main React component
├── package.json        # Node.js dependencies
└── vite.config.js      # Vite configuration
```

## Security Features

- **OAuth 2.0**: Secure authentication with Google
- **Session management**: Server-side session storage
- **Rate limiting**: Protection against abuse and DoS
- **CORS configuration**: Secure cross-origin requests
- **Input validation**: Request data validation
- **File expiry**: Automatic cleanup of expired files
- **Presigned URLs**: Secure direct uploads to R2

## Development Notes

- The application uses WebRTC for P2P file transfers
- WebSocket signaling server handles peer discovery and connection setup
- Files uploaded to cloud storage have configurable expiry times
- The UI closely follows Zapdrop's design patterns and color scheme
- All API endpoints support CORS for development
- Rate limiting is configurable and can be adjusted per endpoint
- Authentication state is managed globally via React Context

## Production Considerations

- Use Redis for rate limiting in production
- Configure proper CORS origins for production
- Set up SSL/TLS certificates
- Use environment variables for all secrets
- Monitor rate limit violations
- Set up log aggregation
- Configure backup strategies for user data
- Implement proper error tracking

## License

This project combines concepts from PairDrop and Zapdrop with original implementation and enhanced features.

