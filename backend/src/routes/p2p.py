import os
import uuid
from flask import Blueprint, request, jsonify

p2p_bp = Blueprint('p2p', __name__)

@p2p_bp.route('/p2p/status', methods=['GET'])
def get_p2p_status():
    """Get P2P connection status"""
    return jsonify({
        'status': 'active',
        'signaling_server': 'connected',
        'message': 'P2P signaling server is running'
    })

@p2p_bp.route('/p2p/room/<room_id>', methods=['GET'])
def get_room_info(room_id):
    """Get information about a P2P room"""
    # This would typically query the WebSocket server state
    # For now, return mock data
    return jsonify({
        'room_id': room_id,
        'peer_count': 0,
        'created_at': '2025-01-01T00:00:00Z'
    })

@p2p_bp.route('/p2p/generate-room', methods=['POST'])
def generate_room():
    """Generate a new P2P room ID"""
    room_id = str(uuid.uuid4())[:8]  # Short room ID
    return jsonify({
        'room_id': room_id,
        'join_url': f'/p2p?room={room_id}'
    })

