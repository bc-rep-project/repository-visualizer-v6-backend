from flask import Blueprint, jsonify, request
from app import limiter, mongo
from app.services.auto_save_service import AutoSaveService

auto_save_bp = Blueprint('auto_save', __name__, url_prefix='/api/repositories')

@auto_save_bp.route('/auto-save/status', methods=['GET'])
@limiter.limit("30/minute")
def get_auto_save_status():
    """Get auto-save service status and statistics."""
    try:
        # Get auto-save service status
        status = AutoSaveService.get_status()
        
        # Get auto-save statistics from MongoDB
        stats = mongo.auto_save_stats.find_one({}, {"_id": 0})
        
        # Combine status and statistics
        return jsonify({
            "status": status,
            "statistics": stats or {}
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error getting auto-save status: {str(e)}"}), 500

@auto_save_bp.route('/auto-save/start', methods=['POST'])
@limiter.limit("10/minute")
def start_auto_save():
    """Start the auto-save service."""
    try:
        # Start the auto-save service
        success = AutoSaveService.start()
        
        if success:
            status = AutoSaveService.get_status()
            return jsonify({
                "message": "Auto-save service started successfully",
                "status": status
            }), 200
        else:
            return jsonify({
                "message": "Auto-save service is already running",
                "status": AutoSaveService.get_status()
            }), 200
    except Exception as e:
        return jsonify({"error": f"Error starting auto-save service: {str(e)}"}), 500

@auto_save_bp.route('/auto-save/stop', methods=['POST'])
@limiter.limit("10/minute")
def stop_auto_save():
    """Stop the auto-save service."""
    try:
        # Stop the auto-save service
        success = AutoSaveService.stop()
        
        if success:
            status = AutoSaveService.get_status()
            return jsonify({
                "message": "Auto-save service stopped successfully",
                "status": status
            }), 200
        else:
            return jsonify({
                "message": "Auto-save service is not running",
                "status": AutoSaveService.get_status()
            }), 200
    except Exception as e:
        return jsonify({"error": f"Error stopping auto-save service: {str(e)}"}), 500

@auto_save_bp.route('/auto-save/run', methods=['POST'])
@limiter.limit("5/minute")
def run_auto_save():
    """Run the auto-save service manually."""
    try:
        # Run the auto-save service manually
        result = AutoSaveService.run_now()
        
        # Update statistics in MongoDB
        mongo.auto_save_stats.update_one(
            {},
            {"$inc": {
                "total_repositories_saved": result["repositories_saved"],
                "total_analyses_saved": result["analyses_saved"],
                "total_enhanced_analyses_saved": result["enhanced_analyses_saved"],
                "total_runs": 1
            },
             "$set": {
                "last_run_time": result["last_run_time"]
             }},
            upsert=True
        )
        
        return jsonify({
            "message": "Auto-save service run manually",
            "repositories_saved": result["repositories_saved"],
            "analyses_saved": result["analyses_saved"],
            "enhanced_analyses_saved": result["enhanced_analyses_saved"],
            "status": AutoSaveService.get_status()
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error running auto-save service: {str(e)}"}), 500 