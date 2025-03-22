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
            "autoSave": {
                "repositories": True,
                "analysis": False,
                "enhancedAnalysis": False,
                "interval": 30
            }
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
        "autoSave": {
            "repositories": True,
            "analysis": False,
            "enhancedAnalysis": False,
            "interval": 30
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
    
    # Get current settings
    settings = mongo.settings.find_one({})
    
    if not settings:
        # If no settings exist, create default settings
        settings = {
            "theme": "light",
            "codeHighlightTheme": "github",
            "defaultVisualization": "graph",
            "autoAnalyze": False,
            "language": "en",
            "autoSave": {
                "repositories": True,
                "analysis": False,
                "enhancedAnalysis": False,
                "interval": 30
            }
        }
        mongo.settings.insert_one(settings)
    
    # Check if autoSave field exists
    if 'autoSave' not in settings:
        settings['autoSave'] = {
            "repositories": True,
            "analysis": False,
            "enhancedAnalysis": False,
            "interval": 30
        }
    
    # Update only the provided auto-save settings
    for key, value in data.items():
        settings['autoSave'][key] = value
    
    # Update settings in the database
    result = mongo.settings.update_one(
        {}, 
        {"$set": {"autoSave": settings['autoSave']}},
        upsert=True
    )
    
    if result.modified_count > 0 or result.upserted_id:
        return jsonify({"message": "Auto-save settings updated successfully", "autoSave": settings['autoSave']})
    else:
        return jsonify({"message": "No changes in auto-save settings", "autoSave": settings['autoSave']}) 