import os
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Optional, Tuple

from .. import db
from ..models.repository import Repository

class RepositoryService:
    @staticmethod
    def check_git_available() -> bool:
        """Check if git is available in the system."""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    @staticmethod
    def clone_repository(repo_url: str, repo_path: str, repo_id: str) -> Tuple[bool, str]:
        """Clone a repository and track its progress."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(repo_path), exist_ok=True)
            
            # Remove existing repo if it exists
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            
            # Clone the repository
            process = subprocess.Popen(
                ['git', 'clone', '--progress', repo_url, repo_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            _, stderr = process.communicate()
            
            if process.returncode == 0:
                return True, "Repository cloned successfully"
            else:
                return False, f"Clone failed: {stderr}"
                
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_repository_stats(repo_path: str) -> Dict[str, int]:
        """Get repository statistics including file count and total size."""
        try:
            file_count = sum([len(files) for _, _, files in os.walk(repo_path)])
            size = sum(os.path.getsize(os.path.join(dirpath, filename))
                      for dirpath, _, filenames in os.walk(repo_path)
                      for filename in filenames)
            
            return {
                'file_count': file_count,
                'size_bytes': size
            }
        except Exception:
            return {'file_count': 0, 'size_bytes': 0}
    
    @staticmethod
    def create_repository(repo_url: str, repo_path: str, repo_id: str) -> Repository:
        """Create a new repository record."""
        repo = Repository(
            repo_id=repo_id,
            name=repo_url.split('/')[-1].replace('.git', ''),
            url=repo_url,
            path=repo_path,
            status='pending'
        )
        db.session.add(repo)
        db.session.commit()
        return repo
    
    @staticmethod
    def update_repository_status(repo: Repository, status: str, stats: Optional[Dict] = None) -> Repository:
        """Update repository status and stats."""
        repo.status = status
        if stats:
            repo.file_count = stats.get('file_count', 0)
            repo.size_bytes = stats.get('size_bytes', 0)
        repo.last_modified = datetime.utcnow()
        db.session.commit()
        return repo
    
    @staticmethod
    def delete_repository(repo: Repository) -> bool:
        """Delete a repository and its files."""
        try:
            if os.path.exists(repo.path):
                shutil.rmtree(repo.path)
            db.session.delete(repo)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False 