from datetime import datetime
from typing import Dict, Optional
from bson import ObjectId

class Repository:
    collection_name = 'repositories'

    def __init__(
        self,
        repo_id: str,
        repo_url: str,
        repo_path: str,
        status: str,
        created_at: datetime,
        updated_at: datetime,
        file_count: int = 0,
        directory_count: int = 0,
        total_size: int = 0,
        languages: Dict[str, int] = None,
        _id: Optional[str] = None
    ):
        self._id = _id
        self.repo_id = repo_id
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.status = status
        self.created_at = created_at if isinstance(created_at, datetime) else datetime.fromisoformat(created_at)
        self.updated_at = updated_at if isinstance(updated_at, datetime) else datetime.fromisoformat(updated_at)
        self.file_count = file_count
        self.directory_count = directory_count
        self.total_size = total_size
        self.languages = languages or {}

    @staticmethod
    def from_db_doc(doc):
        if not doc:
            return None
        repo = Repository(
            repo_id=doc['repo_id'],
            repo_url=doc['repo_url'],
            repo_path=doc['repo_path'],
            status=doc['status'],
            created_at=doc['created_at'],
            updated_at=doc['updated_at'],
            file_count=doc.get('file_count', 0),
            directory_count=doc.get('directory_count', 0),
            total_size=doc.get('total_size', 0),
            languages=doc.get('languages', {}),
            _id=str(doc.get('_id'))
        )
        repo._id = doc.get('_id')
        return repo

    def to_dict(self) -> Dict:
        """Convert repository to dictionary for JSON serialization."""
        return {
            '_id': str(self._id) if self._id else None,
            'repo_id': self.repo_id,
            'repo_url': self.repo_url,
            'repo_path': self.repo_path,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'file_count': self.file_count,
            'directory_count': self.directory_count,
            'total_size': self.total_size,
            'languages': self.languages
        }

    def to_db_dict(self):
        data = self.to_dict()
        data['_id'] = getattr(self, '_id', ObjectId())
        return data 