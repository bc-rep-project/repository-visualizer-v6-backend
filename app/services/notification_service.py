from datetime import datetime
import uuid
from typing import List, Dict, Optional, Any

# In-memory storage for notifications
notifications_store = []

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
            filtered_notifications = notifications_store
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
            total_count = len(notifications_store)
            unread_count = sum(1 for n in notifications_store if not n.get("read", False))
            
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
            for notification in notifications_store:
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
            global notifications_store
            initial_count = len(notifications_store)
            notifications_store = [n for n in notifications_store if n.get("id") != notification_id]
            
            if len(notifications_store) < initial_count:
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
            global notifications_store
            deleted_count = len(notifications_store)
            notifications_store = []
            
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
            
            notifications_store.append(notification)
            return notification
        except Exception as e:
            # Log the error
            print(f"Error adding notification: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Add some sample notifications for testing
def add_sample_notifications():
    # Clear existing notifications
    global notifications_store
    notifications_store = []
    
    # Add sample notifications
    NotificationService.add_notification(
        "Repository 'repository-visualizer-v6-frontend' analyzed successfully.",
        "success",
        {"repository": "repository-visualizer-v6-frontend"}
    )
    
    NotificationService.add_notification(
        "Failed to analyze repository: 'unknown-repo'.",
        "error",
        {"repository": "unknown-repo", "error_code": "REPO_NOT_FOUND"}
    )
    
    NotificationService.add_notification(
        "Repository 'repository-visualizer-v6-backend' has 3 potential security vulnerabilities.",
        "warning",
        {"repository": "repository-visualizer-v6-backend", "vulnerability_count": 3}
    )
    
    NotificationService.add_notification(
        "New version of the application is available.",
        "info",
        {"version": "2.0.0", "release_notes": "https://example.com/release-notes"}
    ) 