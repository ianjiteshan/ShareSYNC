import os
import sys
import uuid
import json
from datetime import datetime, timedelta
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

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'sharesync.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize database
db = init_db(app)

# Enable CORS for all routes
CORS(app, origins="*", supports_credentials=True)

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
    peer_id = str(uuid.uuid4())
    device_info = request.args.get('device_info', 'Unknown Device')
    
    connected_peers[request.sid] = {
        'id': peer_id,
        'name': device_info,
        'status': 'online',
        'connected_at': datetime.utcnow().isoformat(),
        'capabilities': {
            'webrtc': True,
            'file_transfer': True,
            'text_transfer': True
        }
    }
    
    print(f'Peer connected: {peer_id} ({device_info})')
    emit('peer_id', {'peer_id': peer_id, 'device_info': device_info})
    
    # Broadcast peer count to all clients
    emit('peer_count', {'count': len(connected_peers)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_peers:
        peer = connected_peers[request.sid]
        print(f'Peer disconnected: {peer["id"]}')
        
        # Notify other peers in the same room
        for room_id in rooms:
            if request.sid in rooms[room_id]:
                rooms[room_id].remove(request.sid)
                socketio.emit('peer_left', {'peer_id': peer['id']}, room=room_id)
                
        del connected_peers[request.sid]
        
        # Broadcast updated peer count
        emit('peer_count', {'count': len(connected_peers)}, broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id', 'default')
    join_room(room_id)
    
    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(request.sid)
    
    # Send list of peers in the room
    peers_in_room = []
    for sid in rooms[room_id]:
        if sid in connected_peers and sid != request.sid:
            peer_data = connected_peers[sid].copy()
            peer_data['sid'] = sid  # Add session ID for targeting
            peers_in_room.append(peer_data)
    
    emit('peers_list', {'peers': peers_in_room, 'room_id': room_id})
    
    # Notify others about new peer
    if request.sid in connected_peers:
        peer_data = connected_peers[request.sid].copy()
        peer_data['sid'] = request.sid
        emit('peer_joined', peer_data, room=room_id, include_self=False)

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id', 'default')
    leave_room(room_id)
    
    if room_id in rooms and request.sid in rooms[room_id]:
        rooms[room_id].remove(request.sid)
        
        # Notify others about peer leaving
        if request.sid in connected_peers:
            emit('peer_left', {'peer_id': connected_peers[request.sid]['id']}, room=room_id)

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    target_peer = data.get('target_peer')
    offer = data.get('offer')
    
    # Find target peer's socket ID
    target_sid = None
    for sid, peer in connected_peers.items():
        if peer['id'] == target_peer:
            target_sid = sid
            break
    
    if target_sid:
        emit('webrtc_offer', {
            'from_peer': connected_peers[request.sid]['id'],
            'offer': offer,
            'timestamp': datetime.utcnow().isoformat()
        }, room=target_sid)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    target_peer = data.get('target_peer')
    answer = data.get('answer')
    
    # Find target peer's socket ID
    target_sid = None
    for sid, peer in connected_peers.items():
        if peer['id'] == target_peer:
            target_sid = sid
            break
    
    if target_sid:
        emit('webrtc_answer', {
            'from_peer': connected_peers[request.sid]['id'],
            'answer': answer,
            'timestamp': datetime.utcnow().isoformat()
        }, room=target_sid)

@socketio.on('webrtc_ice_candidate')
def handle_ice_candidate(data):
    target_peer = data.get('target_peer')
    candidate = data.get('candidate')
    
    # Find target peer's socket ID
    target_sid = None
    for sid, peer in connected_peers.items():
        if peer['id'] == target_peer:
            target_sid = sid
            break
    
    if target_sid:
        emit('webrtc_ice_candidate', {
            'from_peer': connected_peers[request.sid]['id'],
            'candidate': candidate,
            'timestamp': datetime.utcnow().isoformat()
        }, room=target_sid)

@socketio.on('file_transfer_request')
def handle_file_transfer_request(data):
    target_peer = data.get('target_peer')
    file_info = data.get('file_info')
    
    # Find target peer's socket ID
    target_sid = None
    for sid, peer in connected_peers.items():
        if peer['id'] == target_peer:
            target_sid = sid
            break
    
    if target_sid:
        emit('file_transfer_request', {
            'from_peer': connected_peers[request.sid]['id'],
            'file_info': file_info,
            'timestamp': datetime.utcnow().isoformat()
        }, room=target_sid)

@socketio.on('file_transfer_response')
def handle_file_transfer_response(data):
    target_peer = data.get('target_peer')
    accepted = data.get('accepted', False)
    
    # Find target peer's socket ID
    target_sid = None
    for sid, peer in connected_peers.items():
        if peer['id'] == target_peer:
            target_sid = sid
            break
    
    if target_sid:
        emit('file_transfer_response', {
            'from_peer': connected_peers[request.sid]['id'],
            'accepted': accepted,
            'timestamp': datetime.utcnow().isoformat()
        }, room=target_sid)

@socketio.on('text_message')
def handle_text_message(data):
    target_peer = data.get('target_peer')
    message = data.get('message')
    
    # Find target peer's socket ID
    target_sid = None
    for sid, peer in connected_peers.items():
        if peer['id'] == target_peer:
            target_sid = sid
            break
    
    if target_sid:
        emit('text_message', {
            'from_peer': connected_peers[request.sid]['id'],
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }, room=target_sid)

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

