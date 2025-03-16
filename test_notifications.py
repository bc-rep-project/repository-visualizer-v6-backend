#!/usr/bin/env python3
"""
Test script for notification endpoints.
Run this script to test the notification API endpoints.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def print_response(response):
    """Print the response in a formatted way."""
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("-" * 50)

def test_get_notifications():
    """Test GET /notifications endpoint."""
    print("\n=== Testing GET /notifications ===")
    
    # Test with default parameters
    print("\n1. Get all notifications (default):")
    response = requests.get(f"{BASE_URL}/notifications")
    print_response(response)
    
    # Test with status filter
    print("\n2. Get unread notifications:")
    response = requests.get(f"{BASE_URL}/notifications?status=unread")
    print_response(response)
    
    # Test with type filter
    print("\n3. Get error notifications:")
    response = requests.get(f"{BASE_URL}/notifications?type=error")
    print_response(response)
    
    # Test with multiple filters
    print("\n4. Get unread error and warning notifications:")
    response = requests.get(f"{BASE_URL}/notifications?status=unread&type=error,warning")
    print_response(response)
    
    # Test with pagination
    print("\n5. Get notifications with pagination (limit=2, offset=1):")
    response = requests.get(f"{BASE_URL}/notifications?limit=2&offset=1")
    print_response(response)
    
    # Test with sorting
    print("\n6. Get notifications sorted by timestamp (ascending):")
    response = requests.get(f"{BASE_URL}/notifications?sort=timestamp_asc")
    print_response(response)

def test_add_notification():
    """Test POST /notifications endpoint."""
    print("\n=== Testing POST /notifications ===")
    
    # Test adding a success notification
    print("\n1. Adding a success notification:")
    response = requests.post(
        f"{BASE_URL}/notifications",
        json={
            "message": "Test success notification",
            "type": "success",
            "details": {"test": True, "source": "test_script"}
        }
    )
    print_response(response)
    
    # Test adding an error notification
    print("\n2. Adding an error notification:")
    response = requests.post(
        f"{BASE_URL}/notifications",
        json={
            "message": "Test error notification",
            "type": "error",
            "details": {"test": True, "error_code": "TEST_ERROR"}
        }
    )
    print_response(response)
    
    # Test adding a warning notification
    print("\n3. Adding a warning notification:")
    response = requests.post(
        f"{BASE_URL}/notifications",
        json={
            "message": "Test warning notification",
            "type": "warning"
        }
    )
    print_response(response)
    
    # Test adding an info notification
    print("\n4. Adding an info notification:")
    response = requests.post(
        f"{BASE_URL}/notifications",
        json={
            "message": "Test info notification",
            "type": "info",
            "details": {"test": True, "info": "Additional information"}
        }
    )
    print_response(response)
    
    # Test with invalid type
    print("\n5. Testing with invalid notification type:")
    response = requests.post(
        f"{BASE_URL}/notifications",
        json={
            "message": "Test invalid notification",
            "type": "invalid_type"
        }
    )
    print_response(response)
    
    # Test with missing message
    print("\n6. Testing with missing message field:")
    response = requests.post(
        f"{BASE_URL}/notifications",
        json={
            "type": "info"
        }
    )
    print_response(response)

def test_mark_as_read():
    """Test PATCH /notifications/mark-as-read endpoint."""
    print("\n=== Testing PATCH /notifications/mark-as-read ===")
    
    # First, get all unread notifications
    response = requests.get(f"{BASE_URL}/notifications?status=unread")
    unread_notifications = response.json().get("notifications", [])
    
    if not unread_notifications:
        print("No unread notifications found. Skipping test.")
        return
    
    # Get IDs of unread notifications
    notification_ids = [n.get("id") for n in unread_notifications]
    
    # Mark notifications as read
    print(f"\n1. Marking {len(notification_ids)} notifications as read:")
    response = requests.patch(
        f"{BASE_URL}/notifications/mark-as-read",
        json={"notificationIds": notification_ids}
    )
    print_response(response)
    
    # Verify that notifications are marked as read
    print("\n2. Verifying that notifications are marked as read:")
    response = requests.get(f"{BASE_URL}/notifications?status=unread")
    print_response(response)

def test_delete_notification():
    """Test DELETE /notifications/{id} endpoint."""
    print("\n=== Testing DELETE /notifications/{id} ===")
    
    # First, get all notifications
    response = requests.get(f"{BASE_URL}/notifications")
    notifications = response.json().get("notifications", [])
    
    if not notifications:
        print("No notifications found. Skipping test.")
        return
    
    # Delete the first notification
    notification_id = notifications[0].get("id")
    print(f"\n1. Deleting notification with ID {notification_id}:")
    response = requests.delete(f"{BASE_URL}/notifications/{notification_id}")
    print_response(response)
    
    # Verify that the notification is deleted
    print("\n2. Verifying that the notification is deleted:")
    response = requests.get(f"{BASE_URL}/notifications")
    print_response(response)

def test_delete_all_notifications():
    """Test DELETE /notifications endpoint."""
    print("\n=== Testing DELETE /notifications ===")
    
    # Delete all notifications
    print("\n1. Deleting all notifications:")
    response = requests.delete(f"{BASE_URL}/notifications")
    print_response(response)
    
    # Verify that all notifications are deleted
    print("\n2. Verifying that all notifications are deleted:")
    response = requests.get(f"{BASE_URL}/notifications")
    print_response(response)

def main():
    """Run all tests."""
    try:
        # Check if the server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"Error: Server is not running or not accessible at {BASE_URL}")
            sys.exit(1)
        
        # Run tests
        test_get_notifications()
        test_add_notification()
        test_mark_as_read()
        test_delete_notification()
        test_delete_all_notifications()
        
        print("\nAll tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the server at {BASE_URL}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 