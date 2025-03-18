from flask import Blueprint, jsonify, request
from app import limiter, mongo
from datetime import datetime
import logging

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Initialize default settings with categories matching the UI (theme, visualization, notifications, system)
default_settings = {
    'theme': {
        'mode': 'light',
        'accentColor': '#4a90e2',
        'fontSize': 'medium'
    },
    'visualization': {
        'defaultView': 'forceGraph',
        'enableAnimations': True,
        'nodeSize': 'medium',
        'showLabels': True
    },
    'notifications': {
        'enableSound': True,
        'enablePopups': True,
        'notifyOnUpdates': True,
        'emailNotifications': False
    },
    'system': {
        'autoUpdate': False,
        'updateInterval': 30,  # in minutes
        'logLevel': 'info',
        'dataCache': True
    },
    'last_updated': datetime.utcnow().isoformat()
}

# In a real app, we would load settings from the database
# Here we're using an in-memory store for simplicity
user_settings = dict(default_settings)

@settings_bp.route('', methods=['GET'])
@limiter.limit("30/minute")
def get_settings():
    """
    Get user settings
    ---
    Returns:
        A JSON object containing all user settings
    """
    try:
        return jsonify(user_settings), 200
    except Exception as e:
        logging.error(f"Error fetching settings: {str(e)}")
        return jsonify({"error": "Failed to fetch settings", "message": str(e)}), 500

@settings_bp.route('', methods=['PATCH'])
@limiter.limit("10/minute")
def update_settings():
    """
    Update user settings (partial updates allowed)
    ---
    Parameters:
        - JSON object containing settings to update
    Returns:
        Updated settings
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update settings - handle nested structure
        for category, category_settings in data.items():
            if category in user_settings and isinstance(category_settings, dict):
                # Skip the last_updated field which is handled separately
                if category == 'last_updated':
                    continue
                    
                for key, value in category_settings.items():
                    if key in user_settings[category]:
                        user_settings[category][key] = value
        
        # Update the last_updated timestamp
        user_settings['last_updated'] = datetime.utcnow().isoformat()
        
        return jsonify(user_settings), 200
    except Exception as e:
        logging.error(f"Error updating settings: {str(e)}")
        return jsonify({"error": "Failed to update settings", "message": str(e)}), 500

@settings_bp.route('/reset', methods=['POST'])
@limiter.limit("5/minute")
def reset_settings():
    """
    Reset user settings to default values
    ---
    Returns:
        Default settings
    """
    try:
        global user_settings, default_settings
        # Create a fresh copy of default_settings to ensure we're using the original values
        user_settings = {
            'theme': {
                'mode': 'light',
                'accentColor': '#4a90e2',
                'fontSize': 'medium'
            },
            'visualization': {
                'defaultView': 'forceGraph',
                'enableAnimations': True,
                'nodeSize': 'medium',
                'showLabels': True
            },
            'notifications': {
                'enableSound': True,
                'enablePopups': True,
                'notifyOnUpdates': True,
                'emailNotifications': False
            },
            'system': {
                'autoUpdate': False,
                'updateInterval': 30,  # in minutes
                'logLevel': 'info',
                'dataCache': True
            },
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify(user_settings), 200
    except Exception as e:
        logging.error(f"Error resetting settings: {str(e)}")
        return jsonify({"error": "Failed to reset settings", "message": str(e)}), 500 