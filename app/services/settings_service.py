from typing import Dict, Any, Optional
from app import mongo
from flask import current_app
from bson import ObjectId
import copy

# Get MongoDB connection safely
def get_mongo():
    if hasattr(current_app, 'config') and 'get_mongo_connection' in current_app.config:
        return current_app.config['get_mongo_connection']()
    return mongo

# Default settings to use when a user doesn't have settings yet
DEFAULT_SETTINGS = {
    "theme": {
        "mode": "light",
        "color": "default"
    },
    "visualization": {
        "defaultView": "forceGraph",
        "showLabels": True,
        "labelFontSize": 12
    },
    "notifications": {
        "enableSound": True,
        "showDesktopNotifications": False,
        "notificationTypes": ["error", "warning", "info", "success"]
    },
    "system": {
        "autoUpdate": True,
        "language": "en"
    }
}

class SettingsService:
    @staticmethod
    def get_settings(user_id: str = "default") -> Dict[str, Any]:
        """
        Get settings for a user. If no settings exist, return default settings.
        
        Args:
            user_id: The ID of the user (defaults to "default" for non-authenticated systems)
            
        Returns:
            Dict containing user settings
        """
        try:
            # Try to find existing settings
            settings = get_mongo().db.settings.find_one({"user_id": user_id})
            
            # If settings exist, return them (excluding MongoDB _id)
            if settings:
                if "_id" in settings:
                    settings.pop("_id")
                return settings
            
            # If no settings exist, create default settings for the user
            default_settings = copy.deepcopy(DEFAULT_SETTINGS)
            default_settings["user_id"] = user_id
            
            # Store default settings in the database
            get_mongo().db.settings.insert_one(default_settings)
            
            # Return default settings (without the _id field)
            default_settings.pop("_id", None)
            return default_settings
            
        except Exception as e:
            # Log the error
            print(f"Error getting settings: {str(e)}")
            # Return default settings as fallback
            return copy.deepcopy(DEFAULT_SETTINGS)
    
    @staticmethod
    def update_settings(settings_update: Dict[str, Any], user_id: str = "default") -> Dict[str, Any]:
        """
        Update settings for a user.
        
        Args:
            settings_update: Dict containing the settings to update
            user_id: The ID of the user (defaults to "default" for non-authenticated systems)
            
        Returns:
            Dict containing the updated settings
        """
        try:
            # Get current settings
            current_settings = SettingsService.get_settings(user_id)
            
            # Deep merge the updates into current settings
            updated_settings = SettingsService._deep_merge(current_settings, settings_update)
            
            # Update in the database
            get_mongo().db.settings.update_one(
                {"user_id": user_id},
                {"$set": updated_settings},
                upsert=True
            )
            
            # Return the updated settings
            if "user_id" in updated_settings:
                updated_settings.pop("user_id")
            return updated_settings
            
        except Exception as e:
            # Log the error
            print(f"Error updating settings: {str(e)}")
            return {"error": f"Failed to update settings: {str(e)}"}
    
    @staticmethod
    def reset_to_defaults(category: Optional[str] = None, user_id: str = "default") -> Dict[str, Any]:
        """
        Reset settings to defaults, either all settings or a specific category.
        
        Args:
            category: Optional category to reset (theme, visualization, notifications, system)
            user_id: The ID of the user
            
        Returns:
            Dict containing the updated settings
        """
        try:
            if category:
                # Reset only the specified category
                if category not in DEFAULT_SETTINGS:
                    return {"error": f"Invalid category: {category}"}
                
                update = {category: copy.deepcopy(DEFAULT_SETTINGS[category])}
                return SettingsService.update_settings(update, user_id)
            else:
                # Reset all settings
                default_settings = copy.deepcopy(DEFAULT_SETTINGS)
                default_settings["user_id"] = user_id
                
                # Update in the database
                get_mongo().db.settings.update_one(
                    {"user_id": user_id},
                    {"$set": default_settings},
                    upsert=True
                )
                
                # Return the default settings
                default_settings.pop("user_id")
                return default_settings
                
        except Exception as e:
            # Log the error
            print(f"Error resetting settings: {str(e)}")
            return {"error": f"Failed to reset settings: {str(e)}"}
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, updating nested values.
        
        Args:
            base: Base dictionary
            update: Dictionary with updates
            
        Returns:
            Merged dictionary
        """
        result = copy.deepcopy(base)
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = SettingsService._deep_merge(result[key], value)
            else:
                # Update or add the value
                result[key] = copy.deepcopy(value)
                
        return result 