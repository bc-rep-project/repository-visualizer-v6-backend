from flask import Blueprint, jsonify, request
from app.services.repository_service import RepositoryService
from app.services.notification_service import NotificationService
from app import limiter
from datetime import datetime, timedelta
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
@limiter.limit("50/minute")
def get_repository_pulls(repo_id):
    """Get pull requests for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Generate mock pull requests data
    pulls = []
    now = datetime.utcnow()
    
    statuses = ['open', 'merged', 'closed']
    
    for i in range(8):
        created_date = now - timedelta(days=random.randint(1, 20))
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

@repo_details_bp.route('/<repo_id>/notifications', methods=['GET'])
@limiter.limit("60/minute")
def get_repository_notifications(repo_id):
    """
    Get notifications specific to a repository.
    
    Query parameters:
    - status: Filter by read status ("all", "read", "unread")
    - limit: Maximum number of notifications to return
    - offset: Number of notifications to skip (for pagination)
    """
    try:
        # Check if repository exists
        repo = RepositoryService.get_repository(repo_id)
        if not repo:
            return jsonify({"error": "Repository not found"}), 404
        
        # Parse query parameters
        status = request.args.get('status', 'all')
        if status not in ['all', 'read', 'unread']:
            status = 'all'
        
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
        offset = int(request.args.get('offset', 0))
        
        # Get repository notifications
        result = NotificationService.get_repository_notifications(
            repo_id=repo_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch repository notifications: {str(e)}",
            "total": 0,
            "unread": 0,
            "notifications": []
        }), 500

@repo_details_bp.route('/<repo_id>/notifications', methods=['POST'])
@limiter.limit("30/minute")
def add_repository_notification(repo_id):
    """
    Add a notification for a specific repository.
    
    Request body:
    {
        "message": "Notification message",
        "type": "error" | "warning" | "info" | "success",
        "details": { ... } (optional)
    }
    """
    try:
        # Check if repository exists
        repo = RepositoryService.get_repository(repo_id)
        if not repo:
            return jsonify({"error": "Repository not found"}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request. Request body is required."
            }), 400
        
        # Validate required fields
        if 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Invalid request. 'message' field is required."
            }), 400
            
        if 'type' not in data or data['type'] not in ['error', 'warning', 'info', 'success']:
            return jsonify({
                "success": False,
                "error": "Invalid request. 'type' field must be one of: error, warning, info, success."
            }), 400
        
        # Get repository name
        repo_name = repo.get('repo_name', 'Unknown Repository')
        
        # Create notification
        notification = NotificationService.add_repository_notification(
            repo_id=repo_id,
            repo_name=repo_name,
            message=data['message'],
            notification_type=data['type'],
            details=data.get('details')
        )
        
        return jsonify(notification), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to add repository notification: {str(e)}"
        }), 500

@repo_details_bp.route('/<repo_id>/subscribe', methods=['POST'])
@limiter.limit("30/minute")
def subscribe_to_repository(repo_id):
    """
    Subscribe to notifications for a specific repository.
    
    Request body:
    {
        "subscriberId": "user-id" | "client-id"
    }
    """
    try:
        # Check if repository exists
        repo = RepositoryService.get_repository(repo_id)
        if not repo:
            return jsonify({"error": "Repository not found"}), 404
        
        data = request.get_json()
        
        if not data or 'subscriberId' not in data:
            return jsonify({
                "success": False,
                "error": "Invalid request. 'subscriberId' field is required."
            }), 400
        
        subscriber_id = data['subscriberId']
        
        # Subscribe to repository notifications
        result = NotificationService.subscribe_to_repository(repo_id, subscriber_id)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to subscribe to repository: {str(e)}"
        }), 500

@repo_details_bp.route('/<repo_id>/unsubscribe', methods=['POST'])
@limiter.limit("30/minute")
def unsubscribe_from_repository(repo_id):
    """
    Unsubscribe from notifications for a specific repository.
    
    Request body:
    {
        "subscriberId": "user-id" | "client-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'subscriberId' not in data:
            return jsonify({
                "success": False,
                "error": "Invalid request. 'subscriberId' field is required."
            }), 400
        
        subscriber_id = data['subscriberId']
        
        # Unsubscribe from repository notifications
        result = NotificationService.unsubscribe_from_repository(repo_id, subscriber_id)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to unsubscribe from repository: {str(e)}"
        }), 500 