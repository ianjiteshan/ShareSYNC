import os
import sys
import uuid
import json
from datetime import datetime, timedelta, timezone
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and database
from src.models.database import init_db
from src.models import User, File, Download

# Import routes
from src.routes.user import user_bp
from src.routes.upload import upload_bp
from src.routes.p2p import p2p_bp
from src.routes.auth import auth_bp, init_oauth
from src.routes.files import files_bp
from src.routes.analytics import analytics_bp
from src.routes.cleanup import cleanup_bp, init_cleanup_scheduler
from src.routes.password import password_bp
from src.routes.limits import limits_bp
from src.routes.dashboard import dashboard_bp
from src.routes.security import security_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Get the absolute path for the 'src' directory
basedir = os.path.abspath(os.path.dirname(__file__))
# Define the path for the database directory
db_dir = os.path.join(basedir, 'database')
# Create the directory if it doesn't exist
os.makedirs(db_dir, exist_ok=True)
# Configuration

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'sharesync.db')}")
if os.getenv('FLASK_ENV') == 'development':
    print("Running in Development: Setting SESSION_COOKIE_SECURE = False")
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    print("Running in Production: Setting SESSION_COOKIE_SECURE = True")
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize database
db = init_db(app)

# Enable CORS for all routes
CORS(app, origins="", supports_credentials=True)

# Initialize rate limiter with Redis support
redis_url = os.getenv('REDIS_URL', 'memory://')
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri=redis_url
)

# Initialize OAuth
google_oauth = init_oauth(app)

# Initialize SocketIO for P2P signaling
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(p2p_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(files_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(cleanup_bp, url_prefix='/api')
app.register_blueprint(password_bp, url_prefix='/api')
app.register_blueprint(limits_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(security_bp, url_prefix='/api')

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# Store connected peers for P2P
connected_peers = {}
rooms = {}

# Enhanced P2P WebSocket handlers
@socketio.on('connect')
def handle_connect():
    """
    Client connected to the server.
    We don't do much here, we wait for them to 'join_p2p'.
    """
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """
    Client disconnected from the server.
    """
    print(f"Client disconnected: {request.sid}")
    
    peer_data = connected_peers.pop(request.sid, None)
    
    if peer_data:
        room_id = peer_data.get('room_id')
        if room_id and room_id in rooms:
            # Remove peer from the room list
            if request.sid in rooms[room_id]:
                rooms[room_id].remove(request.sid)

            # Notify all *other* peers in that room
            emit('peer_left', 
                 {'session_id': request.sid}, 
                 room=room_id)
            
            print(f"Peer {request.sid} left room {room_id}")

@socketio.on('join_p2p')
def handle_join_p2p(data):
    """
    This is the event your useP2P.js client sends.
    It replaces your old 'join_room'.
    """
    device_name = data.get('device_name', 'Unknown Device')
    room_id = data.get('room_id', 'default')
    
    join_room(room_id)
    
    # Store peer info
    peer_info = {
        'session_id': request.sid,
        'device_name': device_name,
        'room_id': room_id,
        'joined_at': datetime.now(timezone.utc).isoformat()
    }
    connected_peers[request.sid] = peer_info
    
    # Add to room list
    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(request.sid)
    
    print(f"Peer {request.sid} ({device_name}) joined room {room_id}")

    # 1. Get list of all *other* peers in the same room
    other_peers_in_room = []
    if room_id in rooms:
        for sid in rooms[room_id]:
            if sid != request.sid and sid in connected_peers:
                other_peers_in_room.append(connected_peers[sid])
    
    # 2. Emit 'p2p_joined' *only* to the sender (this is what your client expects)
    emit('p2p_joined', {
        'session_id': request.sid,
        'peers': other_peers_in_room
    })
    
    # 3. Emit 'peer_joined' to all *other* clients in the room
    emit('peer_joined', peer_info, room=room_id, include_self=False)


@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """
    Forward the offer from sender to target.
    We just pass the data along.
    """
    target_session = data.get('target_session')
    if not target_session:
        return

    print(f"Relaying WebRTC offer from {request.sid} to {target_session}")
    
    emit('webrtc_offer', {
        'sender_session': request.sid,
        'offer': data.get('offer')
    }, room=target_session)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    """
    Forward the answer from target back to sender.
    We just pass the data along.
    """
    target_session = data.get('target_session')
    if not target_session:
        return

    print(f"Relaying WebRTC answer from {request.sid} to {target_session}")
    
    emit('webrtc_answer', {
        'sender_session': request.sid,
        'answer': data.get('answer')
    }, room=target_session)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """
    Forward the ICE candidate to the other peer.
    We just pass the data along.
    """
    target_session = data.get('target_session')
    if not target_session:
        return

    # print(f"Relaying ICE candidate from {request.sid} to {target_session}") # This is too noisy
    
    emit('ice_candidate', {
        'sender_session': request.sid,
        'candidate': data.get('candidate')
    }, room=target_session)
    
# @socketio.on('file_transfer_request')
# def handle_file_transfer_request(data):
#     target_peer = data.get('target_peer')
#     file_info = data.get('file_info')
    
#     # Find target peer's socket ID
#     target_sid = None
#     for sid, peer in connected_peers.items():
#         if peer['id'] == target_peer:
#             target_sid = sid
#             break
    
#     if target_sid:
#         emit('file_transfer_request', {
#             'from_peer': connected_peers[request.sid]['id'],
#             'file_info': file_info,
#             'timestamp': datetime.utcnow().isoformat()
#         }, room=target_sid)

# @socketio.on('file_transfer_response')
# def handle_file_transfer_response(data):
#     target_peer = data.get('target_peer')
#     accepted = data.get('accepted', False)
    
#     # Find target peer's socket ID
#     target_sid = None
#     for sid, peer in connected_peers.items():
#         if peer['id'] == target_peer:
#             target_sid = sid
#             break
    
#     if target_sid:
#         emit('file_transfer_response', {
#             'from_peer': connected_peers[request.sid]['id'],
#             'accepted': accepted,
#             'timestamp': datetime.utcnow().isoformat()
#         }, room=target_sid)

# @socketio.on('text_message')
# def handle_text_message(data):
#     target_peer = data.get('target_peer')
#     message = data.get('message')
    
#     # Find target peer's socket ID
#     target_sid = None
#     for sid, peer in connected_peers.items():
#         if peer['id'] == target_peer:
#             target_sid = sid
#             break
    
#     if target_sid:
#         emit('text_message', {
#             'from_peer': connected_peers[request.sid]['id'],
#             'message': message,
#             'timestamp': datetime.utcnow().isoformat()
#         }, room=target_sid)

# Enhanced API endpoints
@app.route('/api/health')
def health_check():
    try:
        # Test database connection
        with app.app_context():
            db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'connected_peers': len(connected_peers),
        'active_rooms': len(rooms),
        'version': '2.0.0'
    })

@app.route('/api/stats')
def get_stats():
    """Get platform statistics"""
    try:
        with app.app_context():
            total_users = User.query.count()
            total_files = File.query.count()
            total_downloads = Download.query.count()
            
            # Files uploaded today
            today = datetime.utcnow().date()
            files_today = File.query.filter(
                db.func.date(File.created_at) == today
            ).count()
            
        return jsonify({
            'total_users': total_users,
            'total_files': total_files,
            'total_downloads': total_downloads,
            'files_today': files_today,
            'connected_peers': len(connected_peers),
            'active_rooms': len(rooms)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms')
def get_active_rooms():
    """Get list of active P2P rooms"""
    room_list = []
    for room_id, sids in rooms.items():
        peers = []
        for sid in sids:
            if sid in connected_peers:
                peer = connected_peers[sid].copy()
                # Remove sensitive information
                peer.pop('sid', None)
                peers.append(peer)
        
        room_list.append({
            'room_id': room_id,
            'peer_count': len(peers),
            'peers': peers
        })
    
    return jsonify({'rooms': room_list})

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Initialize cleanup scheduler
    from src.services.cleanup_service import cleanup_service
    cleanup_service.init_app(app)
    cleanup_service.start_scheduler()
    
    print("🚀 Starting ShareSync - The Ultimate File Sharing Platform")
    print(f"📡 Server running on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🔄 Rate limiting: {redis_url}")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )

