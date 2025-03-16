#!/usr/bin/env python3
"""
Test script for settings endpoints.
Run this script to test the settings API endpoints.
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

def test_get_settings():
    """Test GET /settings endpoint."""
    print("\n=== Testing GET /settings ===")
    
    response = requests.get(f"{BASE_URL}/settings")
    print_response(response)

def test_update_settings():
    """Test PATCH /settings endpoint."""
    print("\n=== Testing PATCH /settings ===")
    
    # Test updating theme mode
    print("\n1. Updating theme mode to dark:")
    response = requests.patch(
        f"{BASE_URL}/settings",
        json={
            "theme": {
                "mode": "dark"
            }
        }
    )
    print_response(response)
    
    # Test updating visualization settings
    print("\n2. Updating visualization settings:")
    response = requests.patch(
        f"{BASE_URL}/settings",
        json={
            "visualization": {
                "showLabels": False,
                "labelFontSize": 14
            }
        }
    )
    print_response(response)
    
    # Test updating multiple categories
    print("\n3. Updating multiple categories:")
    response = requests.patch(
        f"{BASE_URL}/settings",
        json={
            "notifications": {
                "enableSound": False
            },
            "system": {
                "language": "fr"
            }
        }
    )
    print_response(response)
    
    # Test with invalid data
    print("\n4. Testing with invalid data:")
    response = requests.patch(
        f"{BASE_URL}/settings",
        json={
            "invalid_category": {
                "invalid_setting": "value"
            }
        }
    )
    print_response(response)

def test_reset_settings():
    """Test POST /settings/reset endpoint."""
    print("\n=== Testing POST /settings/reset ===")
    
    # Test resetting theme settings
    print("\n1. Resetting theme settings:")
    response = requests.post(f"{BASE_URL}/settings/reset?category=theme")
    print_response(response)
    
    # Test resetting all settings
    print("\n2. Resetting all settings:")
    response = requests.post(f"{BASE_URL}/settings/reset")
    print_response(response)
    
    # Test with invalid category
    print("\n3. Testing with invalid category:")
    response = requests.post(f"{BASE_URL}/settings/reset?category=invalid")
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
        test_get_settings()
        test_update_settings()
        test_reset_settings()
        
        # Get final settings state
        print("\n=== Final Settings State ===")
        response = requests.get(f"{BASE_URL}/settings")
        print_response(response)
        
        print("\nAll tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the server at {BASE_URL}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 