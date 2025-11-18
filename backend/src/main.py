import os
import sys
import uuid
from datetime import datetime, timezone
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# =====================================================
# Load environment variables
# =====================================================
load_dotenv()

    # OAuth REQUIRED fixes — prevents mismatching_state
    # NOTE: The OAUTHLIB_INSECURE_TRANSPORT is a temporary fix for development.
    # The actual fix for mismatching_state is ensuring session cookies are set correctly (SameSite=None, Secure=True).
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_RELAX_REDIRECT_URI'] = '1'

# =====================================================
# Import DB + models
# =====================================================
from src.models.database import init_db
from src.models import User, File, Download

# =====================================================
# Import routes
# =====================================================
from src.routes.user import user_bp
from src.routes.upload import upload_bp        # already has url_prefix="/api"
from src.routes.p2p import p2p_bp
from src.routes.auth import auth_bp, init_oauth
from src.routes.files import files_bp          # already has url_prefix="/api"
from src.routes.analytics import analytics_bp
from src.routes.cleanup import cleanup_bp, init_cleanup_scheduler
from src.routes.password import password_bp
from src.routes.limits import limits_bp
from src.routes.dashboard import dashboard_bp
from src.routes.security import security_bp

# =====================================================
# App initialization
# =====================================================
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Database directory
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')
os.makedirs(db_dir, exist_ok=True)

# =====================================================
# Flask Configuration
# =====================================================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'sharesync.db')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH_BYTES', 500 * 1024 * 1024))

# =====================================================
# Cookie + OAuth Session Settings
# =====================================================
if os.getenv('FLASK_ENV') == 'development':
    print("Running in Development: Setting SESSION_COOKIE_SECURE=False + SameSite=Lax")
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    print("Running in Production: Strict cookies (SameSite=None, Secure=True for cross-origin OAuth)")
    # For cross-origin OAuth flow (frontend on one domain, backend on another), 
    # the session cookie must be Secure and SameSite=None.
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# =====================================================
# Init DB
# =====================================================
db = init_db(app)

# =====================================================
# CORS Configuration
# =====================================================
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})

# =====================================================
# Rate Limiting
# =====================================================
redis_url = os.getenv('REDIS_URL', 'memory://')
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri=redis_url
)

# =====================================================
# OAuth Initialization
# =====================================================
google_oauth = init_oauth(app)

# =====================================================
# Socket.IO
# =====================================================
socketio = SocketIO(app, cors_allowed_origins="*")

connected_peers = {}
rooms = {}

# =====================================================
# WebSocket Handlers
# =====================================================
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    peer = connected_peers.pop(request.sid, None)
    if peer:
        room_id = peer.get("room_id")
        print(f"Peer {request.sid} left room {room_id}")
        if room_id in rooms and request.sid in rooms[room_id]:
            rooms[room_id].remove(request.sid)
            emit("peer_left", {"session_id": request.sid}, room=room_id)

@socketio.on('join_p2p')
def handle_join(data):
    device = data.get("device_name", "Unknown Device")
    room_id = data.get("room_id", "default")

    join_room(room_id)

    peer_info = {
        "session_id": request.sid,
        "device_name": device,
        "room_id": room_id,
        "joined_at": datetime.now(timezone.utc).isoformat()
    }

    connected_peers[request.sid] = peer_info

    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(request.sid)

    print(f"Peer {request.sid} ({device}) joined {room_id}")

    other_peers = [
        connected_peers[sid]
        for sid in rooms[room_id] if sid != request.sid and sid in connected_peers
    ]

    emit("p2p_joined", {
        "session_id": request.sid,
        "peers": other_peers
    })

    emit("peer_joined", peer_info, room=room_id, include_self=False)

@socketio.on('webrtc_offer')
def handle_offer(data):
    target = data.get("target_session")
    if target:
        emit("webrtc_offer", {
            "sender_session": request.sid,
            "offer": data.get("offer")
        }, room=target)

@socketio.on('webrtc_answer')
def handle_answer(data):
    target = data.get("target_session")
    if target:
        emit("webrtc_answer", {
            "sender_session": request.sid,
            "answer": data.get("answer")
        }, room=target)

@socketio.on('ice_candidate')
def handle_candidate(data):
    target = data.get("target_session")
    if target:
        emit("ice_candidate", {
            "sender_session": request.sid,
            "candidate": data.get("candidate")
        }, room=target)

# =====================================================
# API Routes
# =====================================================

# DO NOT ADD url_prefix — upload_bp & files_bp ALREADY have /api inside them
app.register_blueprint(upload_bp)
app.register_blueprint(files_bp)

# Other blueprints require /api prefix
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(p2p_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(cleanup_bp, url_prefix='/api')
app.register_blueprint(password_bp, url_prefix='/api')
app.register_blueprint(limits_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(security_bp, url_prefix='/api')

# =====================================================
# Health + Stats
# =====================================================
@app.route("/api/health")
def health():
    try:
        db.session.execute("SELECT 1")
        status = "connected"
    except:
        status = "error"

    return jsonify({
        "status": "healthy",
        "database": status,
        "connected_peers": len(connected_peers),
        "active_rooms": len(rooms)
    })

@app.route("/api/stats")
def stats():
    with app.app_context():
        return jsonify({
            "total_users": User.query.count(),
            "total_files": File.query.count(),
            "total_downloads": Download.query.count(),
        })

# =====================================================
# React Frontend Serving
# =====================================================
@app.route("/", defaults={'path': ''})
@app.route("/<path:path>")
def serve(path):
    static_folder = app.static_folder
    if path and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)

    index_path = os.path.join(static_folder, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(static_folder, "index.html")

    return "index.html not found", 404

# =====================================================
# Start App
# =====================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_ENV") == "development"

    try:
        init_cleanup_scheduler(app)
    except:
        pass

    print("⚠ Development Mode: Cookie settings for OAuth loosened" if debug else "Production Mode")

    print("🚀 Starting ShareSync")
    print(f"📡 Port: {port}")
    print(f"🌐 Frontend Allowed: {FRONTEND_ORIGIN}")

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )
