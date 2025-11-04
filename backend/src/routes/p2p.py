from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room, rooms
import uuid
from datetime import datetime

from ..middleware.rate_limiter import api_rate_limit

p2p_bp = Blueprint('p2p', __name__)

# Store active P2P sessions
active_sessions = {}
peer_connections = {}

@p2p_bp.route('/p2p/status', methods=['GET'])
def get_p2p_status():
    """Get P2P connection status"""
    return jsonify({
        'status': 'active',
        'signaling_server': 'connected',
        'message': 'P2P signaling server is running',
        'authentication_required': False,
        'features': {
            'max_file_size': 'unlimited',
            'encryption': 'end-to-end',
            'connection_type': 'WebRTC P2P'
        }
    })

@p2p_bp.route('/p2p/join', methods=['POST'])
@api_rate_limit
def join_p2p_network():
    """Join the P2P network without authentication"""
    try:
        data = request.get_json() or {}
        device_name = data.get('device_name', f'Device_{uuid.uuid4().hex[:8]}')
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store session info
        active_sessions[session_id] = {
            'device_name': device_name,
            'joined_at': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'status': 'active'
        }
        
        return jsonify({
            'session_id': session_id,
            'device_name': device_name,
            'message': 'Successfully joined P2P network',
            'network_info': {
                'total_peers': len(active_sessions),
                'your_ip': request.remote_addr
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to join P2P network: {str(e)}'}), 500

@p2p_bp.route('/p2p/peers', methods=['GET'])
@api_rate_limit
def get_available_peers():
    """Get list of available peers for P2P connection"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        # Filter out current session from peer list
        available_peers = []
        for sid, session_info in active_sessions.items():
            if sid != session_id:
                available_peers.append({
                    'session_id': sid,
                    'device_name': session_info['device_name'],
                    'status': session_info['status'],
                    'joined_at': session_info['joined_at']
                })
        
        return jsonify({
            'peers': available_peers,
            'total_peers': len(available_peers),
            'your_session': session_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get peers: {str(e)}'}), 500

@p2p_bp.route('/p2p/leave', methods=['POST'])
@api_rate_limit
def leave_p2p_network():
    """Leave the P2P network"""
    try:
        session_id = request.headers.get('X-Session-ID')
        
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        # Clean up any peer connections
        if session_id in peer_connections:
            del peer_connections[session_id]
        
        return jsonify({
            'message': 'Successfully left P2P network',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to leave P2P network: {str(e)}'}), 500

@p2p_bp.route('/p2p/room/<room_id>', methods=['GET'])
def get_room_info(room_id):
    """Get information about a P2P room"""
    # Count peers in this room
    room_peers = [s for s in active_sessions.values() if s.get('room_id') == room_id]
    
    return jsonify({
        'room_id': room_id,
        'peer_count': len(room_peers),
        'created_at': datetime.utcnow().isoformat(),
        'authentication_required': False
    })

@p2p_bp.route('/p2p/generate-room', methods=['POST'])
def generate_room():
    """Generate a new P2P room ID"""
    room_id = str(uuid.uuid4())[:8]  # Short room ID
    return jsonify({
        'room_id': room_id,
        'join_url': f'/p2p?room={room_id}',
        'authentication_required': False
    })

@p2p_bp.route('/p2p/stats', methods=['GET'])
@api_rate_limit
def get_p2p_stats():
    """Get P2P network statistics (public endpoint)"""
    try:
        # Calculate stats
        total_sessions = len(active_sessions)
        active_connections = len(peer_connections)
        
        # Get network activity (last hour)
        current_time = datetime.utcnow()
        recent_sessions = 0
        
        for session_info in active_sessions.values():
            joined_time = datetime.fromisoformat(session_info['joined_at'])
            time_diff = (current_time - joined_time).total_seconds()
            if time_diff < 3600:  # Last hour
                recent_sessions += 1
        
        return jsonify({
            'network_stats': {
                'total_active_sessions': total_sessions,
                'active_connections': active_connections,
                'recent_sessions_1h': recent_sessions,
                'network_status': 'online' if total_sessions > 0 else 'idle'
            },
            'features': {
                'authentication_required': False,
                'max_file_size': 'unlimited',
                'encryption': 'end-to-end',
                'connection_type': 'WebRTC P2P',
                'cost': 'free'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get P2P stats: {str(e)}'}), 500

