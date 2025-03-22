#!/usr/bin/env python3
import requests
import json
import subprocess
import os
import sys

def check_if_flask_running():
    """Check if Flask application is running on port 8000"""
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.ConnectionError:
        return False

def main():
    # Check if Flask is running
    if not check_if_flask_running():
        print("Flask server is not running. Starting it...")
        print("Please wait while the server starts...")
        # Start Flask in a background process
        flask_process = subprocess.Popen(
            ["source venv/bin/activate && python app.py"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Wait for Flask to start
        for _ in range(10):
            if check_if_flask_running():
                print("Flask server started successfully!")
                break
            import time
            time.sleep(1)
        else:
            print("Failed to start Flask server.")
            return
    
    # Now use the API to check for backups by triggering a manual auto-save
    print("Checking MongoDB auto-save backups via Flask API...")
    try:
        # Run auto-save manually to ensure data is saved
        response = requests.post("http://localhost:8000/api/repositories/auto-save/run")
        if response.status_code == 200:
            result = response.json()
            print(f"Auto-save completed with {result.get('saved', 0)} repositories saved")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Last run: {result.get('last_run', 'N/A')}")
            
            # Now count the backups
            settings_response = requests.get("http://localhost:8000/api/settings")
            if settings_response.status_code == 200:
                settings = settings_response.json()
                auto_save_settings = settings.get('auto_save', {})
                print(f"\nAuto-save settings:")
                print(f"Enabled: {auto_save_settings.get('enabled', False)}")
                print(f"Interval: {auto_save_settings.get('interval', 0)} seconds")
                print(f"Last run: {auto_save_settings.get('last_run', 'N/A')}")
            
            # Get backups through the new endpoint
            print("\nChecking backups through the dedicated endpoint...")
            backups_response = requests.get("http://localhost:8000/api/repositories/auto-save/backups")
            if backups_response.status_code == 200:
                backups_data = backups_response.json()
                total_backups = backups_data.get('total', 0)
                backups = backups_data.get('backups', [])
                print(f"Total backups in MongoDB: {total_backups}")
                
                if total_backups > 0:
                    print("\nDetails of most recent backups:")
                    for i, backup in enumerate(backups[:3]):  # Show up to 3 backups
                        print(f"\nBackup #{i+1}:")
                        print(f"  ID: {backup.get('_id')}")
                        print(f"  Repository ID: {backup.get('repository_id')}")
                        print(f"  Repository URL: {backup.get('repo_url')}")
                        print(f"  Repository Name: {backup.get('repo_name')}")
                        print(f"  Backed up at: {backup.get('backed_up_at')}")
                        print(f"  File count: {backup.get('file_count')}")
                        print(f"  Directory count: {backup.get('directory_count')}")
                        print(f"  Total size: {backup.get('total_size')}")
                else:
                    print("No backups found in MongoDB. The auto-save feature might not be working correctly.")
            
            # Get first repository to check detailed backup
            repos_response = requests.get("http://localhost:8000/api/repositories?limit=1")
            if repos_response.status_code == 200:
                repos_data = repos_response.json()
                repos = repos_data.get('repositories', [])
                if repos:
                    repo_id = repos[0].get('_id')
                    print(f"\nChecking backup for repository: {repo_id}")
                    
                    # Save one repository and get details
                    save_response = requests.post(f"http://localhost:8000/api/repositories/auto-save/{repo_id}")
                    if save_response.status_code == 200:
                        save_result = save_response.json()
                        print(f"Repository saved: {save_result.get('status', 'unknown')}")
                        print(f"Message: {save_result.get('message', 'N/A')}")
                        
                        # Check backups again to see if the count increased
                        backups_response = requests.get("http://localhost:8000/api/repositories/auto-save/backups")
                        if backups_response.status_code == 200:
                            backups_data = backups_response.json()
                            new_total = backups_data.get('total', 0)
                            print(f"\nUpdated backup count: {new_total}")
                            if new_total > total_backups:
                                print("Auto-save feature is working correctly - backup count increased!")
                            else:
                                print("Warning: Backup count did not increase after saving a repository.")
        else:
            print(f"Error running auto-save: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()