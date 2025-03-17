from flask import Blueprint, jsonify, request
from app.services.settings_service import SettingsService
from app import limiter

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
@limiter.limit("60/minute")
def get_settings():
    """
    Get all settings for the current user.
    
    Returns:
        JSON object containing all user settings
    """
    try:
        # In a real application, you would get the user ID from the authenticated session
        # For simplicity, we're using a default user ID
        user_id = "default"
        
        # Get settings from the service
        settings = SettingsService.get_settings(user_id)
        
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch settings: {str(e)}"
        }), 500

@settings_bp.route('', methods=['PATCH'])
@limiter.limit("30/minute")
def update_settings():
    """
    Update settings for the current user.
    
    Request body:
        JSON object containing the settings to update
        
    Returns:
        JSON object containing the updated settings
    """
    try:
        # Get the request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid request. Request body is required."
            }), 400
        
        # Validate the data structure
        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request. Settings must be a JSON object."
            }), 400
            
        # Check for allowed top-level keys
        allowed_keys = ['theme', 'visualization', 'notifications', 'system']
        for key in data.keys():
            if key not in allowed_keys:
                return jsonify({
                    "error": f"Invalid setting key: '{key}'. Allowed keys are: {', '.join(allowed_keys)}"
                }), 400
        
        # In a real application, you would get the user ID from the authenticated session
        user_id = "default"
        
        # Update settings
        updated_settings = SettingsService.update_settings(data, user_id)
        
        # Check if there was an error
        if isinstance(updated_settings, dict) and "error" in updated_settings:
            return jsonify(updated_settings), 500
        
        return jsonify(updated_settings), 200
    except ValueError as e:
        return jsonify({
            "error": f"Invalid JSON format: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "error": f"Failed to update settings: {str(e)}"
        }), 500

@settings_bp.route('/reset', methods=['POST'])
@limiter.limit("10/minute")
def reset_settings():
    """
    Reset settings to defaults.
    
    Query parameters:
        category: Optional category to reset (theme, visualization, notifications, system)
        
    Returns:
        JSON object containing the reset settings
    """
    try:
        # Get the category from query parameters
        category = request.args.get('category')
        
        # In a real application, you would get the user ID from the authenticated session
        user_id = "default"
        
        # Reset settings
        reset_settings = SettingsService.reset_to_defaults(category, user_id)
        
        # Check if there was an error
        if "error" in reset_settings:
            return jsonify(reset_settings), 400 if "Invalid category" in reset_settings.get("error", "") else 500
        
        return jsonify(reset_settings), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to reset settings: {str(e)}"
        }), 500 