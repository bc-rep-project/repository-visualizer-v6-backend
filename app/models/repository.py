from datetime import datetime
from .. import db

class Repository(db.Model):
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    repo_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    file_count = db.Column(db.Integer, default=0)
    size_bytes = db.Column(db.BigInteger, default=0)
    status = db.Column(db.String(50), default='pending')
    cloned_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
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