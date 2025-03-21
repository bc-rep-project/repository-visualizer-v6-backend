from flask import Blueprint, jsonify, request
from app import limiter, mongo
from app.services.repository_service import RepositoryService
from datetime import datetime, timedelta
from bson import ObjectId
import random

repo_details_bp = Blueprint('repository_details', __name__, url_prefix='/api/repositories')

@repo_details_bp.route('/<repo_id>/commits', methods=['GET'])
@limiter.limit("50/minute")
def get_repository_commits(repo_id):
    """Get commits for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Generate mock commits data
    commits = []
    now = datetime.utcnow()
    
    for i in range(20):
        commit_date = now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        commits.append({
            'id': f'commit_{i}_{repo_id}',
            'message': f'Update code and fix issues #{i}',
            'author': {
                'name': 'Developer Name',
                'email': 'developer@example.com'
            },
            'date': commit_date.isoformat(),
            'stats': {
                'additions': random.randint(5, 100),
                'deletions': random.randint(1, 50),
                'files_changed': random.randint(1, 10)
            }
        })
    
    return jsonify(commits), 200

@repo_details_bp.route('/<repo_id>/issues', methods=['GET'])
@limiter.limit("50/minute")
def get_repository_issues(repo_id):
    """Get issues for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Generate mock issues data
    issues = []
    now = datetime.utcnow()
    
    statuses = ['open', 'closed', 'in_progress']
    priorities = ['low', 'medium', 'high', 'critical']
    
    for i in range(10):
        created_date = now - timedelta(days=random.randint(1, 30))
        issues.append({
            'id': f'issue_{i}_{repo_id}',
            'title': f'Issue #{i}: Fix bug in component',
            'description': f'This is a detailed description of issue #{i}',
            'status': random.choice(statuses),
            'priority': random.choice(priorities),
            'created_at': created_date.isoformat(),
            'updated_at': (created_date + timedelta(days=random.randint(0, 5))).isoformat(),
            'author': 'Developer Name'
        })
    
    return jsonify(issues), 200

@repo_details_bp.route('/<repo_id>/issues', methods=['POST'])
@limiter.limit("20/minute")
def create_repository_issue(repo_id):
    """Create a new issue for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    # Create mock issue
    now = datetime.utcnow()
    issue = {
        'id': f'issue_new_{repo_id}_{now.timestamp()}',
        'title': title,
        'description': description or '',
        'status': 'open',
        'priority': 'medium',
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'author': 'Current User'
    }
    
    return jsonify(issue), 201

@repo_details_bp.route('/<repo_id>/pulls', methods=['GET'])
@limiter.limit("60/minute")
def get_repository_pulls(repo_id):
    """Get pull requests for the repository."""
    # Check if repository exists
    repo = RepositoryService.get_repository(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    
    # Generate mock pull requests data
    pulls = []
    statuses = ['open', 'closed', 'merged']
    
    # Create between 0 and 10 sample pull requests
    num_pulls = random.randint(0, 10)
    
    for i in range(1, num_pulls + 1):
        created_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        pulls.append({
            'id': f'pull_{i}_{repo_id}',
            'title': f'Pull Request #{i}: Implement new feature',
            'description': f'This pull request implements feature #{i}',
            'status': random.choice(statuses),
            'created_at': created_date.isoformat(),
            'updated_at': (created_date + timedelta(days=random.randint(0, 3))).isoformat(),
            'author': 'Developer Name',
            'branch': f'feature/new-feature-{i}'
        })
    
    return jsonify(pulls), 200 