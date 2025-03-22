import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bson import ObjectId
import os

from app import mongo
from app.services.repository_service import RepositoryService

class AutoSaveService:
    _instance = None
    _running = False
    _thread = None
    _last_run_time = None
    _next_run_time = None
    _repositories_saved = 0
    _analyses_saved = 0
    _enhanced_analyses_saved = 0

    @classmethod
    def get_instance(cls):
        """Get singleton instance of AutoSaveService"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def start(cls):
        """Start the auto-save service"""
        instance = cls.get_instance()
        if not cls._running:
            cls._running = True
            cls._thread = threading.Thread(target=instance._run_service, daemon=True)
            cls._thread.start()
            return True
        return False
    
    @classmethod
    def stop(cls):
        """Stop the auto-save service"""
        if cls._running:
            cls._running = False
            cls._thread = None
            return True
        return False
    
    @classmethod
    def is_running(cls):
        """Check if the auto-save service is running"""
        return cls._running
    
    @classmethod
    def get_status(cls):
        """Get the status of the auto-save service"""
        return {
            "running": cls._running,
            "last_run_time": cls._last_run_time,
            "next_run_time": cls._next_run_time,
            "repositories_saved": cls._repositories_saved,
            "analyses_saved": cls._analyses_saved,
            "enhanced_analyses_saved": cls._enhanced_analyses_saved
        }
    
    @classmethod
    def run_now(cls):
        """Run the auto-save service immediately"""
        instance = cls.get_instance()
        result = instance._perform_auto_save()
        return {
            "running": cls._running,
            "repositories_saved": result["repositories_saved"],
            "analyses_saved": result["analyses_saved"],
            "enhanced_analyses_saved": result["enhanced_analyses_saved"],
            "last_run_time": cls._last_run_time
        }
    
    def _run_service(self):
        """Run the auto-save service in a background thread"""
        while self._running:
            # Get settings to determine auto-save interval
            settings = mongo.settings.find_one({})
            
            # Default to 30 minutes if settings not found
            interval_minutes = 30
            if settings and 'autoSave' in settings and 'interval' in settings['autoSave']:
                interval_minutes = int(settings['autoSave']['interval'])
            
            # Update next run time
            self.__class__._next_run_time = (datetime.utcnow() + timedelta(minutes=interval_minutes)).isoformat() + 'Z'
            
            # Perform auto-save operations
            self._perform_auto_save()
            
            # Sleep for the interval
            sleep_seconds = interval_minutes * 60
            for _ in range(sleep_seconds):
                if not self._running:
                    break
                time.sleep(1)  # Check every second if we should stop
    
    def _perform_auto_save(self):
        """Perform auto-save operations"""
        # Get settings to determine which auto-save operations to perform
        settings = mongo.settings.find_one({})
        
        save_repositories = True
        save_analysis = False
        save_enhanced_analysis = False
        
        if settings and 'autoSave' in settings:
            save_repositories = settings['autoSave'].get('repositories', True)
            save_analysis = settings['autoSave'].get('analysis', False)
            save_enhanced_analysis = settings['autoSave'].get('enhancedAnalysis', False)
        
        # Track saved counts
        repos_saved = 0
        analysis_saved = 0
        enhanced_saved = 0
        
        # Auto-save repositories
        if save_repositories:
            repos_saved = self._save_repositories()
        
        # Auto-save analysis
        if save_analysis:
            analysis_saved = self._save_analyses()
        
        # Auto-save enhanced analysis
        if save_enhanced_analysis:
            enhanced_saved = self._save_enhanced_analyses()
        
        # Update statistics
        self.__class__._last_run_time = datetime.utcnow().isoformat() + 'Z'
        self.__class__._repositories_saved = repos_saved
        self.__class__._analyses_saved = analysis_saved
        self.__class__._enhanced_analyses_saved = enhanced_saved
        
        return {
            "repositories_saved": repos_saved,
            "analyses_saved": analysis_saved,
            "enhanced_analyses_saved": enhanced_saved
        }
    
    def _save_repositories(self):
        """Save all repositories to MongoDB"""
        try:
            # Get all completed repositories
            repositories = RepositoryService.get_all_repositories({"status": "completed"})
            
            # Count of repos saved
            count = 0
            
            # Update each repository
            for repo in repositories:
                repo_id = repo.get('_id')
                repo_path = repo.get('repo_path')
                
                # Skip if repo path doesn't exist
                if not repo_path or not os.path.exists(repo_path):
                    continue
                
                # Get latest stats
                try:
                    stats = RepositoryService._get_repository_stats(repo_path)
                    
                    # Update repository
                    mongo.repositories.update_one(
                        {'_id': ObjectId(repo_id)},
                        {'$set': {
                            'file_count': stats['file_count'],
                            'directory_count': stats['directory_count'],
                            'total_size': stats['total_size'],
                            'languages': stats['languages'],
                            'updated_at': datetime.utcnow().isoformat() + 'Z',
                            'last_auto_save': datetime.utcnow().isoformat() + 'Z'
                        }}
                    )
                    count += 1
                except Exception as e:
                    print(f"Error saving repository {repo_id}: {e}")
            
            return count
        except Exception as e:
            print(f"Error in _save_repositories: {e}")
            return 0
    
    def _save_analyses(self):
        """Save all repository analyses to MongoDB"""
        try:
            # Get all completed repositories
            repositories = RepositoryService.get_all_repositories({"status": "completed"})
            
            # Count of analyses saved
            count = 0
            
            # Update each repository analysis
            for repo in repositories:
                repo_id = repo.get('_id')
                
                # Skip if repo doesn't exist
                if not repo_id:
                    continue
                
                try:
                    # Perform analysis
                    analysis = RepositoryService.analyze_repository_code(str(repo_id))
                    
                    # Skip if analysis failed
                    if not analysis or 'error' in analysis:
                        continue
                    
                    # Save analysis to MongoDB
                    mongo.repository_analyses.update_one(
                        {'repository_id': str(repo_id)},
                        {'$set': {
                            'repository_id': str(repo_id),
                            'analysis': analysis,
                            'updated_at': datetime.utcnow().isoformat() + 'Z',
                            'last_auto_save': datetime.utcnow().isoformat() + 'Z'
                        }},
                        upsert=True
                    )
                    count += 1
                except Exception as e:
                    print(f"Error saving analysis for repository {repo_id}: {e}")
            
            return count
        except Exception as e:
            print(f"Error in _save_analyses: {e}")
            return 0
    
    def _save_enhanced_analyses(self):
        """Save all enhanced repository analyses to MongoDB"""
        try:
            # Get all completed repositories
            repositories = RepositoryService.get_all_repositories({"status": "completed"})
            
            # Count of enhanced analyses saved
            count = 0
            
            # Import enhanced repository service only when needed 
            # to avoid circular imports
            from app.services.enhanced_repository_service import EnhancedRepositoryService
            
            # Update each repository enhanced analysis
            for repo in repositories:
                repo_id = repo.get('_id')
                
                # Skip if repo doesn't exist
                if not repo_id:
                    continue
                
                try:
                    # Perform enhanced analysis
                    enhanced_analysis = EnhancedRepositoryService.analyze_repository_code(str(repo_id))
                    
                    # Skip if analysis failed
                    if not enhanced_analysis or 'error' in enhanced_analysis:
                        continue
                    
                    # Save enhanced analysis to MongoDB
                    mongo.enhanced_repository_analyses.update_one(
                        {'repository_id': str(repo_id)},
                        {'$set': {
                            'repository_id': str(repo_id),
                            'enhanced_analysis': enhanced_analysis,
                            'updated_at': datetime.utcnow().isoformat() + 'Z',
                            'last_auto_save': datetime.utcnow().isoformat() + 'Z'
                        }},
                        upsert=True
                    )
                    count += 1
                except Exception as e:
                    print(f"Error saving enhanced analysis for repository {repo_id}: {e}")
            
            return count
        except Exception as e:
            print(f"Error in _save_enhanced_analyses: {e}")
            return 0 