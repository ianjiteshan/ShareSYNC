

### 1. Install MinIO (for cloud storage)
```bash
# Download and install MinIO server
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create data directory
mkdir -p ~/minio-data

# Start MinIO server
minio server ~/minio-data --console-address ":9001"
```

MinIO will be available at:
- API: http://localhost:9000
- Console: http://localhost:9001
- Default credentials: minioadmin / minioadmin

### 2. Install Node.js Dependencies
```bash
cd enhanced-file-share
npm install socket.io-client
```

## Backend Setup

### 1. Install Python Dependencies
```bash
cd enhanced-file-share-backend
source venv/bin/activate
pip install boto3 python-socketio flask-socketio
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and update:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```env
# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-actual-google-client-id
GOOGLE_CLIENT_SECRET=your-actual-google-client-secret

# MinIO (use defaults for local development)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sharesync-files

# Flask
FLASK_SECRET_KEY=your-random-secret-key
```

### 3. Start Backend
```bash
cd enhanced-file-share-backend
source venv/bin/activate
python src/main.py
```

## Frontend Setup

### 1. Update Vite Config
Add proxy configuration to `vite.config.js`:
```javascript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```

### 2. Start Frontend
```bash
cd enhanced-file-share
npm run dev
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:5001/api/auth/callback`
   - `http://localhost:5173/api/auth/callback`

## Testing the Application

### 1. P2P Sharing (No Auth Required)
- Open http://localhost:5173
- Click "Share Locally (P2P)"
- Select files and send to discovered devices
- Works without any login

### 2. Cloud Upload (Auth Required)
- Open http://localhost:5173
- Click "Upload to Cloud"
- Sign in with Google
- Upload files with expiry and password options

## File Structure Core

- `enhanced-file-share-backend/src/services/minio_client.py` - Real MinIO storage
- `enhanced-file-share/src/hooks/useP2P.js` - Real WebRTC P2P implementation
- `enhanced-file-share-backend/src/routes/auth.py` - Fixed Google auth
- `enhanced-file-share-backend/src/routes/upload.py` - Real MinIO integration
- `enhanced-file-share-backend/src/routes/p2p.py` - Real P2P signaling
- `enhanced-file-share/src/components/P2PPage.jsx` - Real P2P interface
- `enhanced-file-share/src/App.jsx` - Removed auth from P2P routes



### ✅ Real P2P Sharing
- WebRTC peer-to-peer connections
- Socket.IO signaling server
- Real file transfer with progress
- Device discovery on local network
- No authentication required

### ✅ Real Cloud Storage
- MinIO S3-compatible storage
- File upload with metadata
- Password protection
- Expiry management
- Google OAuth authentication

### ✅ Security Features
- Rate limiting on all endpoints
- File type validation
- Size limits for cloud uploads
- Password hashing for protected files

## Troubleshooting

### MinIO Connection Issues
- Ensure MinIO is running on port 9000
- Check firewall settings
- Verify credentials in .env file

### P2P Connection Issues
- Ensure both devices are on same network
- Check WebSocket connection to backend
- Verify STUN servers are accessible

### Google Auth Issues
- Check OAuth credentials in Google Console
- Verify redirect URIs are correct
- Ensure Google+ API is enabled

## Production Deployment

For production deployment:
1. Use PostgreSQL instead of in-memory storage
2. Use Redis for rate limiting
3. Set up proper SSL certificates
4. Configure production MinIO with proper credentials
5. Use environment-specific OAuth credentials
