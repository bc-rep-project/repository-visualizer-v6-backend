import os
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import current_app
from ..models.repository import Repository

class RepositoryService:
    @staticmethod
    def get_all_repositories() -> List[Repository]:
        """Get all repositories from the database."""
        return list(current_app.mongo.db.repositories.find())

    @staticmethod
    def get_repository(repo_id: str) -> Optional[Repository]:
        """Get a repository by its ID."""
        repo_data = current_app.mongo.db.repositories.find_one({'repo_id': repo_id})
        return Repository(**repo_data) if repo_data else None

    @staticmethod
    def create_repository(repo_url: str, repo_path: str, repo_id: str) -> Repository:
        """Create a new repository record."""
        repo = Repository(
            repo_id=repo_id,
            repo_url=repo_url,
            repo_path=repo_path,
            status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        current_app.mongo.db.repositories.insert_one(repo.to_dict())
        return repo

    @staticmethod
    def update_repository_status(repo: Repository, status: str, stats: Dict = None) -> Repository:
        """Update repository status and stats."""
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        if stats:
            update_data.update(stats)
        
        current_app.mongo.db.repositories.update_one(
            {'repo_id': repo.repo_id},
            {'$set': update_data}
        )
        
        repo_data = current_app.mongo.db.repositories.find_one({'repo_id': repo.repo_id})
        return Repository(**repo_data)

    @staticmethod
    def delete_repository(repo: Repository) -> bool:
        """Delete a repository and its files."""
        try:
            # Delete local repository files
            if os.path.exists(repo.repo_path):
                shutil.rmtree(repo.repo_path)
            
            # Delete from database
            current_app.mongo.db.repositories.delete_one({'repo_id': repo.repo_id})
            return True
        except Exception as e:
            current_app.logger.error(f"Error deleting repository: {str(e)}")
            return False

    @staticmethod
    def check_git_available() -> bool:
        """Check if git is available on the system."""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def clone_repository(repo_url: str, repo_path: str, repo_id: str) -> Tuple[bool, str]:
        """Clone a repository to the local filesystem."""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)

            os.makedirs(os.path.dirname(repo_path), exist_ok=True)
            
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, repo_path],
                capture_output=True,
                text=True,
                check=True
            )
            return True, "Repository cloned successfully"
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip()
            return False, f"Git clone failed: {error_message}"
        except Exception as e:
            return False, f"Error cloning repository: {str(e)}"

    @staticmethod
    def get_repository_stats(repo_path: str) -> Dict:
        """Get repository statistics."""
        stats = {
            'file_count': 0,
            'directory_count': 0,
            'total_size': 0,
            'languages': {}
        }

        try:
            for root, dirs, files in os.walk(repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                
                stats['directory_count'] += len(dirs)
                stats['file_count'] += len(files)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    stats['total_size'] += os.path.getsize(file_path)
                    
                    # Count files by extension
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        stats['languages'][ext] = stats['languages'].get(ext, 0) + 1

        except Exception as e:
            current_app.logger.error(f"Error getting repository stats: {str(e)}")
        
        return stats 