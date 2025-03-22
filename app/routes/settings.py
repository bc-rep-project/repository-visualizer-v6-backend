from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from app import mongo
from app.services.auto_save_service import AutoSaveService

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get application settings."""
    settings = mongo.settings.find_one({}, {"_id": 0})
    if not settings:
        # If no settings exist, create default settings
        default_settings = {
            "theme": "light",
            "codeHighlightTheme": "github",
            "defaultVisualization": "graph",
            "autoAnalyze": False,
            "language": "en",
            "auto_save": {
                "enabled": False,
                "interval": 3600,  # 1 hour in seconds
                "last_run": None
            }
        }
        mongo.settings.insert_one(default_settings)
        settings = default_settings
    
    # If auto_save settings don't exist, add them
    if "auto_save" not in settings:
        settings["auto_save"] = {
            "enabled": False,
            "interval": 3600,  # 1 hour in seconds
            "last_run": None
        }
        mongo.settings.update_one({}, {"$set": {"auto_save": settings["auto_save"]}})
    
    return jsonify(settings)

@settings_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update application settings."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Update settings in the database
    result = mongo.settings.update_one(
        {}, 
        {"$set": data},
        upsert=True
    )
    
    if result.modified_count > 0 or result.upserted_id:
        return jsonify({"message": "Settings updated successfully"})
    else:
        return jsonify({"message": "No changes in settings"})

@settings_bp.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """Reset settings to default values."""
    default_settings = {
        "theme": "light",
        "codeHighlightTheme": "github",
        "defaultVisualization": "graph",
        "autoAnalyze": False,
        "language": "en",
        "auto_save": {
            "enabled": False,
            "interval": 3600,  # 1 hour in seconds
            "last_run": None
        }
    }
    
    mongo.settings.delete_many({})
    mongo.settings.insert_one(default_settings)
    
    return jsonify({"message": "Settings reset to defaults", "settings": default_settings})

@settings_bp.route('/api/settings/auto-save', methods=['PATCH'])
def update_auto_save_settings():
    """Update auto-save settings."""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Extract auto-save specific settings
    enabled = data.get('enabled')
    interval = data.get('interval')
    
    if enabled is None and interval is None:
        return jsonify({"error": "No auto-save settings provided"}), 400
    
    # Update settings and start/stop auto-save as needed
    if enabled is True:
        result = AutoSaveService.start_auto_save(interval)
        return jsonify(result), 200
    elif enabled is False:
        result = AutoSaveService.stop_auto_save()
        return jsonify(result), 200
    elif interval is not None:
        # Just update the interval if provided
        try:
            interval = int(interval)
            if interval < 300:  # Minimum 5 minutes
                return jsonify({"error": "Interval must be at least 300 seconds (5 minutes)"}), 400
            
            # Update interval in settings
            mongo.settings.update_one(
                {}, 
                {"$set": {"auto_save.interval": interval}},
                upsert=True
            )
            
            # If auto-save is running, update the interval
            if AutoSaveService.get_status()["running"]:
                AutoSaveService.stop_auto_save()
                result = AutoSaveService.start_auto_save(interval)
                return jsonify(result), 200
            else:
                return jsonify({
                    "status": "updated", 
                    "message": f"Auto-save interval updated to {interval} seconds"
                }), 200
            
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid interval value"}), 400
    
    return jsonify({"error": "Invalid auto-save settings"}), 400 