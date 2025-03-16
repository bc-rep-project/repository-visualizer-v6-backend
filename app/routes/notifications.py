from flask import Blueprint, jsonify, request
from app.services.notification_service import NotificationService, add_sample_notifications
from app import limiter

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Initialize sample notifications when the module is loaded
add_sample_notifications()

@notifications_bp.route('', methods=['GET'])
@limiter.limit("60/minute")
def get_notifications():
    """
    Get notifications with optional filtering and sorting.
    
    Query parameters:
    - status: Filter by read status ("all", "read", "unread")
    - type: Filter by notification types (comma-separated list of "error", "warning", "info", "success")
    - limit: Maximum number of notifications to return
    - offset: Number of notifications to skip (for pagination)
    - sort: Sort order ("timestamp_desc" or "timestamp_asc")
    """
    try:
        # Parse query parameters
        status = request.args.get('status', 'all')
        if status not in ['all', 'read', 'unread']:
            status = 'all'
        
        types_param = request.args.get('type')
        types = types_param.split(',') if types_param else None
        
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
        offset = int(request.args.get('offset', 0))
        sort = request.args.get('sort', 'timestamp_desc')
        if sort not in ['timestamp_desc', 'timestamp_asc']:
            sort = 'timestamp_desc'
        
        # Get notifications
        result = NotificationService.get_notifications(
            status=status,
            types=types,
            limit=limit,
            offset=offset,
            sort=sort
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch notifications: {str(e)}",
            "total": 0,
            "unread": 0,
            "notifications": []
        }), 500

@notifications_bp.route('', methods=['POST'])
@limiter.limit("60/minute")
def add_notification():
    """
    Add a new notification.
    
    Request body:
    {
        "message": "Notification message",
        "type": "error" | "warning" | "info" | "success",
        "details": { ... } (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request. Request body is required."
            }), 400
        
        # Validate required fields
        if 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Invalid request. 'message' field is required."
            }), 400
            
        if 'type' not in data or data['type'] not in ['error', 'warning', 'info', 'success']:
            return jsonify({
                "success": False,
                "error": "Invalid request. 'type' field must be one of: error, warning, info, success."
            }), 400
        
        # Create notification
        notification = NotificationService.add_notification(
            message=data['message'],
            notification_type=data['type'],
            details=data.get('details')
        )
        
        return jsonify(notification), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to add notification: {str(e)}"
        }), 500

@notifications_bp.route('/mark-as-read', methods=['PATCH'])
@limiter.limit("60/minute")
def mark_notifications_as_read():
    """
    Mark specified notifications as read.
    
    Request body:
    {
        "notificationIds": ["id1", "id2", ...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'notificationIds' not in data or not isinstance(data['notificationIds'], list):
            return jsonify({
                "success": False,
                "error": "Invalid request. Expected 'notificationIds' array in request body."
            }), 400
        
        notification_ids = data['notificationIds']
        result = NotificationService.mark_as_read(notification_ids)
        
        if result.get('success', False):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to mark notifications as read: {str(e)}"
        }), 500

@notifications_bp.route('', methods=['DELETE'])
@limiter.limit("30/minute")
def delete_all_notifications():
    """Delete all notifications."""
    try:
        result = NotificationService.delete_all_notifications()
        
        if result.get('success', False):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete notifications: {str(e)}"
        }), 500

@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@limiter.limit("60/minute")
def delete_notification(notification_id):
    """Delete a specific notification."""
    try:
        result = NotificationService.delete_notification(notification_id)
        
        if result.get('success', False):
            return jsonify(result), 200
        else:
            return jsonify(result), 404 if result.get('error') == 'Notification not found' else 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete notification: {str(e)}"
        }), 500 