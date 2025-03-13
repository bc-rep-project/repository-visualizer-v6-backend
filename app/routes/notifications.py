from flask import Blueprint, jsonify, request
from app import limiter
from datetime import datetime, timedelta
import random

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Mock notifications (in a real app, these would be stored in the database)
notifications = []

# Generate some mock notifications
now = datetime.utcnow()
for i in range(10):
    notification_date = now - timedelta(days=i, hours=random.randint(0, 23))
    notifications.append({
        'id': f'notification_{i}',
        'title': f'Notification #{i}',
        'message': f'This is notification #{i} with some details about a repository event.',
        'type': random.choice(['info', 'warning', 'error', 'success']),
        'read': random.choice([True, False]),
        'created_at': notification_date.isoformat()
    })

@notifications_bp.route('', methods=['GET'])
@limiter.limit("30/minute")
def get_notifications():
    """Get user notifications."""
    # Optional filter for unread notifications
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    
    if unread_only:
        filtered_notifications = [n for n in notifications if not n['read']]
    else:
        filtered_notifications = notifications
    
    return jsonify({
        'notifications': filtered_notifications,
        'unread_count': len([n for n in notifications if not n['read']])
    }), 200

@notifications_bp.route('/<notification_id>/read', methods=['POST'])
@limiter.limit("50/minute")
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    for notification in notifications:
        if notification['id'] == notification_id:
            notification['read'] = True
            return jsonify(notification), 200
    
    return jsonify({'error': 'Notification not found'}), 404

@notifications_bp.route('/read-all', methods=['POST'])
@limiter.limit("10/minute")
def mark_all_read():
    """Mark all notifications as read."""
    for notification in notifications:
        notification['read'] = True
    
    return jsonify({
        'success': True,
        'message': 'All notifications marked as read'
    }), 200 