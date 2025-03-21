from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from app import mongo

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
        }
        mongo.settings.insert_one(default_settings)
        settings = default_settings
    
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
    }
    
    mongo.settings.delete_many({})
    mongo.settings.insert_one(default_settings)
    
    return jsonify({"message": "Settings reset to defaults", "settings": default_settings}) 