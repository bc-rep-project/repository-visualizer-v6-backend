import os
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app import mongo
from bson import ObjectId
from app.services.repository_service import RepositoryService

class AutoSaveService:
    """Service for automatically saving repository data to MongoDB."""
    
    # Class variables for thread management
    _auto_save_thread = None
    _running = False
    _interval = 60 * 60  # Default: 1 hour in seconds
    
    @classmethod
    def start_auto_save(cls, interval: int = None) -> Dict:
        """Start the auto-save background thread.
        
        Args:
            interval: Time between saves in seconds. Defaults to 1 hour.
        
        Returns:
            Dict: Status message
        """
        if cls._running:
            return {"status": "already_running", "message": "Auto-save is already running"}
        
        # Update interval if provided
        if interval is not None:
            cls._interval = max(300, min(86400, interval))  # Limit between 5 min and 24 hours
        
        # Start thread
        cls._running = True
        cls._auto_save_thread = threading.Thread(target=cls._auto_save_worker, daemon=True)
        cls._auto_save_thread.start()
        
        # Update settings to reflect auto-save is enabled
        cls._update_settings(True, cls._interval)
        
        return {
            "status": "started", 
            "message": f"Auto-save started with {cls._interval} seconds interval", 
            "interval": cls._interval
        }
    
    @classmethod
    def stop_auto_save(cls) -> Dict:
        """Stop the auto-save background thread.
        
        Returns:
            Dict: Status message
        """
        if not cls._running:
            return {"status": "not_running", "message": "Auto-save is not running"}
        
        cls._running = False
        # Thread will terminate on next cycle due to _running flag
        
        # Update settings to reflect auto-save is disabled
        cls._update_settings(False, cls._interval)
        
        return {"status": "stopped", "message": "Auto-save stopped"}
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get the current status of auto-save.
        
        Returns:
            Dict: Status information
        """
        settings = mongo.settings.find_one({}, {"_id": 0}) or {}
        auto_save_config = settings.get("auto_save", {})
        
        return {
            "running": cls._running,
            "interval": cls._interval,
            "enabled": auto_save_config.get("enabled", False),
            "last_run": auto_save_config.get("last_run", None),
            "next_run": None if not cls._running else (
                (datetime.fromisoformat(auto_save_config.get("last_run", datetime.utcnow().isoformat())) + 
                timedelta(seconds=cls._interval)).isoformat()
            )
        }
    
    @classmethod
    def _update_settings(cls, enabled: bool, interval: int) -> None:
        """Update auto-save settings in the database.
        
        Args:
            enabled: Whether auto-save is enabled
            interval: Time between saves in seconds
        """
        last_run = datetime.utcnow().isoformat()
        
        mongo.settings.update_one(
            {}, 
            {"$set": {
                "auto_save": {
                    "enabled": enabled,
                    "interval": interval,
                    "last_run": last_run
                }
            }},
            upsert=True
        )
    
    @classmethod
    def _auto_save_worker(cls) -> None:
        """Background worker that runs the auto-save process periodically."""
        print("Auto-save thread started")
        
        while cls._running:
            try:
                cls.run_auto_save()
                
                # Sleep for the configured interval
                # We check _running periodically to allow for quicker shutdown
                for _ in range(cls._interval // 10):
                    if not cls._running:
                        break
                    time.sleep(10)
                
                # For any remaining time less than 10 seconds
                remaining = cls._interval % 10
                if remaining > 0 and cls._running:
                    time.sleep(remaining)
                    
            except Exception as e:
                print(f"Error in auto-save thread: {e}")
                # Sleep for 5 minutes before retrying after error
                time.sleep(300)
    
    @classmethod
    def run_auto_save(cls) -> Dict:
        """Run a single auto-save operation.
        
        This saves all repository data to MongoDB.
        
        Returns:
            Dict: Result of the operation
        """
        print("Running auto-save operation...")
        start_time = time.time()
        saved_count = 0
        error_count = 0
        
        try:
            # Get all repositories that are in 'completed' status
            repos = list(mongo.db.repositories.find({"status": "completed"}))
            total = len(repos)
            
            for repo in repos:
                repo_id = str(repo.get("_id"))
                try:
                    # Save repository data
                    saved = cls._save_repository_data(repo_id)
                    if saved:
                        saved_count += 1
                except Exception as e:
                    print(f"Error saving repository {repo_id}: {e}")
                    error_count += 1
            
            # Update last run time
            last_run = datetime.utcnow().isoformat()
            mongo.settings.update_one(
                {}, 
                {"$set": {"auto_save.last_run": last_run}},
                upsert=True
            )
            
            elapsed = time.time() - start_time
            return {
                "status": "completed",
                "message": f"Auto-save completed in {elapsed:.2f} seconds",
                "total": total,
                "saved": saved_count,
                "errors": error_count,
                "last_run": last_run
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "status": "error",
                "message": f"Auto-save failed after {elapsed:.2f} seconds: {str(e)}",
                "error": str(e)
            }
    
    @classmethod
    def _save_repository_data(cls, repo_id: str) -> bool:
        """Save a repository's data to MongoDB.
        
        Args:
            repo_id: The repository ID to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get repository
        repo = RepositoryService.get_repository(repo_id)
        if not repo:
            return False
        
        # Create or update MongoDB backup collection
        backup_data = {
            "repository_id": ObjectId(repo_id),
            "repo_url": repo.get("repo_url"),
            "repo_name": repo.get("repo_name"),
            "file_count": repo.get("file_count"),
            "directory_count": repo.get("directory_count"),
            "total_size": repo.get("total_size"),
            "languages": repo.get("languages", {}),
            "backed_up_at": datetime.utcnow().isoformat()
        }
        
        # If repository has a file structure, include it
        repo_path = repo.get("repo_path")
        if repo_path and os.path.exists(repo_path):
            try:
                # Get repository structure
                structure = RepositoryService.analyze_repository_code(repo_id)
                if structure and not isinstance(structure, dict) or not structure.get("error"):
                    backup_data["structure"] = structure
            except Exception as e:
                print(f"Error getting repository structure for {repo_id}: {e}")
        
        # Use upsert to create or update record
        mongo.db.repository_backups.update_one(
            {"repository_id": ObjectId(repo_id)},
            {"$set": backup_data},
            upsert=True
        )
        
        return True
    
    @classmethod
    def save_repository(cls, repo_id: str) -> Dict:
        """Manually save a specific repository's data to MongoDB.
        
        Args:
            repo_id: The repository ID to save
            
        Returns:
            Dict: Result of the operation
        """
        try:
            success = cls._save_repository_data(repo_id)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Repository {repo_id} saved successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Repository {repo_id} not found or could not be saved"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error saving repository {repo_id}: {str(e)}",
                "error": str(e)
            } 