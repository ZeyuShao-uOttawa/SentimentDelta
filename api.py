"""
Simple API endpoints for the Flask app
"""
from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'SentimentDelta API is running',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'sentimentdelta'
    }), 200