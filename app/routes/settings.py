from flask import Blueprint, jsonify, request
from app import limiter, mongo
from datetime import datetime

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Mock settings (in a real app, these would be stored in the database)
app_settings = {
    'theme': 'light',
    'max_repo_size_mb': 500,
    'default_visualization': 'graph',
    'enable_animations': True,
    'auto_refresh': False,
    'refresh_interval_seconds': 30,
    'notifications_enabled': True,
    'last_updated': datetime.utcnow().isoformat()
}

@settings_bp.route('', methods=['GET'])
@limiter.limit("30/minute")
def get_settings():
    """Get application settings."""
    return jsonify(app_settings), 200

@settings_bp.route('', methods=['PUT'])
@limiter.limit("10/minute")
def update_settings():
    """Update application settings."""
    data = request.get_json()
    
    # Update settings
    for key, value in data.items():
        if key in app_settings:
            app_settings[key] = value
    
    app_settings['last_updated'] = datetime.utcnow().isoformat()
    
    return jsonify(app_settings), 200 