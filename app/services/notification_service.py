from datetime import datetime
import uuid
import time
from typing import List, Dict, Optional, Any

# In-memory storage for notifications
notifications_db = []
repo_subscriptions = {}  # Mapping of repo_id to list of subscribers

def add_sample_notifications():
    """Add sample notifications to the database for testing."""
    if not notifications_db:
        notifications_db.extend([
            {
                'id': str(uuid.uuid4()),
                'message': 'Welcome to Repository Visualizer',
                'type': 'info',
                'timestamp': datetime.now().isoformat(),
                'read': False,
                'details': {
                    'title': 'Getting Started',
                    'description': 'Explore the features of Repository Visualizer to analyze your code repositories.'
                }
            },
            {
                'id': str(uuid.uuid4()),
                'message': 'New repository analysis available',
                'type': 'success',
                'timestamp': (datetime.now().timestamp() - 3600) * 1000,  # 1 hour ago
                'read': False,
                'details': {
                    'repoId': 'sample-repo-id',
                    'repoName': 'Sample Repository'
                }
            },
            {
                'id': str(uuid.uuid4()),
                'message': 'Failed to clone repository',
                'type': 'error',
                'timestamp': (datetime.now().timestamp() - 86400) * 1000,  # 1 day ago
                'read': True,
                'details': {
                    'repoUrl': 'https://github.com/invalid/repo',
                    'error': 'Authentication failed'
                }
            }
        ])

class NotificationService:
    @staticmethod
    def get_notifications(
        status: str = "all",
        types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "timestamp_desc"
    ) -> Dict[str, Any]:
        """
        Get notifications with optional filtering and sorting.
        
        Args:
            status: Filter by read status ("all", "read", "unread")
            types: Filter by notification types (list of "error", "warning", "info", "success")
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip (for pagination)
            sort: Sort order ("timestamp_desc" or "timestamp_asc")
            
        Returns:
            Dictionary with total count, unread count, and filtered notifications
        """
        try:
            # Filter by status
            filtered_notifications = notifications_db
            if status == "read":
                filtered_notifications = [n for n in filtered_notifications if n.get("read", False)]
            elif status == "unread":
                filtered_notifications = [n for n in filtered_notifications if not n.get("read", False)]
            
            # Filter by types
            if types:
                filtered_notifications = [n for n in filtered_notifications if n.get("type") in types]
            
            # Sort notifications
            if sort == "timestamp_asc":
                filtered_notifications.sort(key=lambda n: n.get("timestamp", ""))
            else:  # Default to timestamp_desc
                filtered_notifications.sort(key=lambda n: n.get("timestamp", ""), reverse=True)
            
            # Apply pagination
            paginated_notifications = filtered_notifications[offset:offset + limit]
            
            # Count total and unread
            total_count = len(notifications_db)
            unread_count = sum(1 for n in notifications_db if not n.get("read", False))
            
            return {
                "total": total_count,
                "unread": unread_count,
                "notifications": paginated_notifications
            }
        except Exception as e:
            # Log the error
            print(f"Error getting notifications: {str(e)}")
            # Return empty result with error flag
            return {
                "total": 0,
                "unread": 0,
                "notifications": [],
                "error": str(e)
            }
    
    @staticmethod
    def get_repository_notifications(repo_id: str, status: str = 'all', 
                                   limit: int = 50, offset: int = 0) -> Dict:
        """
        Get notifications specific to a repository.
        
        Args:
            repo_id: Repository ID to filter by
            status: Filter by read status ("all", "read", "unread")
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip (for pagination)
        
        Returns:
            Dict containing notifications and metadata
        """
        # Filter by repository ID
        repo_notifications = [n for n in notifications_db 
                            if 'details' in n and 'repoId' in n['details'] and n['details']['repoId'] == repo_id]
        
        # Filter by status
        if status == 'read':
            filtered = [n for n in repo_notifications if n.get('read', False)]
        elif status == 'unread':
            filtered = [n for n in repo_notifications if not n.get('read', False)]
        else:
            filtered = repo_notifications.copy()
        
        # Count unread
        unread_count = sum(1 for n in repo_notifications if not n.get('read', False))
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Paginate
        paginated = filtered[offset:offset + limit]
        
        return {
            'total': len(repo_notifications),
            'unread': unread_count,
            'notifications': paginated
        }
    
    @staticmethod
    def add_notification(
        message: str,
        notification_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a new notification.
        
        Args:
            message: The notification message
            notification_type: Type of notification ("error", "warning", "info", "success")
            details: Optional additional details
            
        Returns:
            The created notification object
        """
        try:
            notification = {
                "id": str(uuid.uuid4()),
                "type": notification_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "read": False
            }
            
            if details:
                notification["details"] = details
            
            notifications_db.append(notification)
            return notification
        except Exception as e:
            # Log the error
            print(f"Error adding notification: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def add_repository_notification(repo_id: str, repo_name: str, message: str, 
                                 notification_type: str, details: Optional[Dict] = None) -> Dict:
        """
        Add a notification related to a specific repository.
        
        Args:
            repo_id: Repository ID
            repo_name: Repository name
            message: Notification message
            notification_type: Type of notification ('error', 'warning', 'info', 'success')
            details: Additional details for the notification
        
        Returns:
            The created notification
        """
        details = details or {}
        details['repoId'] = repo_id
        details['repoName'] = repo_name
        
        notification = NotificationService.add_notification(message, notification_type, details)
        
        # Notify subscribers if any
        if repo_id in repo_subscriptions:
            # In a real app, this would trigger real-time notifications to subscribers
            pass
        
        return notification
    
    @staticmethod
    def mark_as_read(notification_ids: List[str]) -> Dict[str, Any]:
        """
        Mark specified notifications as read.
        
        Args:
            notification_ids: List of notification IDs to mark as read
            
        Returns:
            Dictionary with success status and count of updated notifications
        """
        try:
            updated_count = 0
            for notification in notifications_db:
                if notification.get("id") in notification_ids and not notification.get("read", False):
                    notification["read"] = True
                    updated_count += 1
            
            return {
                "success": True,
                "updated_count": updated_count
            }
        except Exception as e:
            # Log the error
            print(f"Error marking notifications as read: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def delete_notification(notification_id: str) -> Dict[str, Any]:
        """
        Delete a specific notification.
        
        Args:
            notification_id: ID of the notification to delete
            
        Returns:
            Dictionary with success status
        """
        try:
            global notifications_db
            initial_count = len(notifications_db)
            notifications_db = [n for n in notifications_db if n.get("id") != notification_id]
            
            if len(notifications_db) < initial_count:
                return {"success": True}
            else:
                return {"success": False, "error": "Notification not found"}
        except Exception as e:
            # Log the error
            print(f"Error deleting notification: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def delete_all_notifications() -> Dict[str, Any]:
        """
        Delete all notifications.
        
        Returns:
            Dictionary with success status and count of deleted notifications
        """
        try:
            global notifications_db
            deleted_count = len(notifications_db)
            notifications_db = []
            
            return {
                "success": True,
                "deleted_count": deleted_count
            }
        except Exception as e:
            # Log the error
            print(f"Error deleting all notifications: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def subscribe_to_repository(repo_id: str, subscriber_id: str) -> Dict:
        """
        Subscribe to notifications for a specific repository.
        
        Args:
            repo_id: Repository ID
            subscriber_id: ID of the subscriber (user ID, client ID, etc.)
        
        Returns:
            Dict with success status
        """
        if repo_id not in repo_subscriptions:
            repo_subscriptions[repo_id] = []
        
        if subscriber_id not in repo_subscriptions[repo_id]:
            repo_subscriptions[repo_id].append(subscriber_id)
        
        return {
            'success': True,
            'subscribed': True
        }
    
    @staticmethod
    def unsubscribe_from_repository(repo_id: str, subscriber_id: str) -> Dict:
        """
        Unsubscribe from notifications for a specific repository.
        
        Args:
            repo_id: Repository ID
            subscriber_id: ID of the subscriber
        
        Returns:
            Dict with success status
        """
        if repo_id in repo_subscriptions and subscriber_id in repo_subscriptions[repo_id]:
            repo_subscriptions[repo_id].remove(subscriber_id)
            return {
                'success': True,
                'unsubscribed': True
            }
        
        return {
            'success': False,
            'error': 'Subscription not found'
        } 