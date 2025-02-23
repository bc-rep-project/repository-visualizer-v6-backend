from datetime import datetime
from bson import ObjectId

class Repository:
    collection_name = 'repositories'

    def __init__(self, repo_id, name, url, path, status='pending'):
        self.repo_id = repo_id
        self.name = name
        self.url = url
        self.path = path
        self.file_count = 0
        self.size_bytes = 0
        self.status = status
        self.cloned_at = datetime.utcnow()
        self.last_modified = datetime.utcnow()

    @staticmethod
    def from_db_doc(doc):
        if not doc:
            return None
        repo = Repository(
            repo_id=doc['repo_id'],
            name=doc['name'],
            url=doc['url'],
            path=doc['path'],
            status=doc['status']
        )
        repo.file_count = doc.get('file_count', 0)
        repo.size_bytes = doc.get('size_bytes', 0)
        repo.cloned_at = doc.get('cloned_at', datetime.utcnow())
        repo.last_modified = doc.get('last_modified', datetime.utcnow())
        repo._id = doc.get('_id')
        return repo

    def to_dict(self):
        return {
            'id': str(getattr(self, '_id', None)),
            'repo_id': self.repo_id,
            'name': self.name,
            'url': self.url,
            'path': self.path,
            'file_count': self.file_count,
            'size_bytes': self.size_bytes,
            'status': self.status,
            'cloned_at': self.cloned_at.isoformat(),
            'last_modified': self.last_modified.isoformat()
        }

    def to_db_dict(self):
        data = self.to_dict()
        data['_id'] = getattr(self, '_id', ObjectId())
        data['cloned_at'] = self.cloned_at
        data['last_modified'] = self.last_modified
        return data 