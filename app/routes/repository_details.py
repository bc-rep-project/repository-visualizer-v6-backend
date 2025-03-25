from flask import Blueprint, jsonify, request
from app import limiter, mongo
from app.services.repository_service import RepositoryService
from datetime import datetime, timedelta
from bson import ObjectId
import random
import os
import requests

repo_details_bp = Blueprint('repository_details', __name__, url_prefix='/api/repositories')

@repo_details_bp.route('/<repo_id>/github', methods=['GET'])
@limiter.limit("30/minute")
def get_github_data(repo_id):
    """Get GitHub data for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Check if repo_url is a GitHub URL
    repo_url = repository.get('repo_url', '')
    if 'github.com' not in repo_url:
        return jsonify({'error': 'Not a GitHub repository', 'url': repo_url}), 400
    
    # Extract owner and repo name from URL
    try:
        # Handle both HTTPS and SSH URLs
        owner = None
        repo_name = None
        
        if repo_url.startswith('git@github.com:'):
            # SSH format
            parts = repo_url.replace('git@github.com:', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1].replace('.git', '')
        else:
            # HTTPS format
            parts = repo_url.strip('/').split('/')
            if len(parts) >= 4 and parts[-3] == 'github.com':
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
        
        if not owner or not repo_name:
            return jsonify({'error': 'Could not parse GitHub repository URL'}), 400
        
        # Get GitHub token from environment variable
        github_token = os.environ.get('GITHUB_TOKEN', '')
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Fetch repository data from GitHub API
        repo_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}',
            headers=headers
        )
        
        if repo_response.status_code != 200:
            return jsonify({'error': f'GitHub API error: {repo_response.status_code}', 'details': repo_response.text}), 400
        
        repo_data = repo_response.json()
        
        # Fetch additional data (commits, issues, pull requests)
        commits_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/commits?per_page=10',
            headers=headers
        )
        commits = commits_response.json() if commits_response.status_code == 200 else []
        
        issues_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/issues?state=all&per_page=10',
            headers=headers
        )
        issues = issues_response.json() if issues_response.status_code == 200 else []
        
        # Filter out pull requests from issues (GitHub API includes PRs in issues endpoint)
        issues = [issue for issue in issues if 'pull_request' not in issue]
        
        pulls_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/pulls?state=all&per_page=10',
            headers=headers
        )
        pulls = pulls_response.json() if pulls_response.status_code == 200 else []
        
        contributors_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/contributors?per_page=10',
            headers=headers
        )
        contributors = contributors_response.json() if contributors_response.status_code == 200 else []
        
        # Try to get README content
        readme = None
        try:
            readme_response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo_name}/readme',
                headers=headers
            )
            if readme_response.status_code == 200:
                readme = readme_response.json()
        except Exception as e:
            print(f"Error fetching README: {e}")
        
        # Combine all data
        github_data = {
            'repository': repo_data,
            'commits': commits,
            'issues': issues,
            'pulls': pulls,
            'contributors': contributors,
            'readme': readme
        }
        
        return jsonify(github_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_details_bp.route('/<repo_id>/github/commits', methods=['GET'])
@limiter.limit("50/minute")
def get_github_commits(repo_id):
    """Get GitHub commits for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Check if repo_url is a GitHub URL
    repo_url = repository.get('repo_url', '')
    if 'github.com' not in repo_url:
        return jsonify({'error': 'Not a GitHub repository', 'url': repo_url}), 400
    
    # Extract owner and repo name
    try:
        # Handle both HTTPS and SSH URLs
        owner = None
        repo_name = None
        
        if repo_url.startswith('git@github.com:'):
            # SSH format
            parts = repo_url.replace('git@github.com:', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1].replace('.git', '')
        else:
            # HTTPS format
            parts = repo_url.strip('/').split('/')
            if len(parts) >= 4 and parts[-3] == 'github.com':
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
        
        if not owner or not repo_name:
            return jsonify({'error': 'Could not parse GitHub repository URL'}), 400
        
        # Get GitHub token from environment variable
        github_token = os.environ.get('GITHUB_TOKEN', '')
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Fetch commits directly from GitHub API
        commits_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/commits?per_page=10',
            headers=headers
        )
        
        if commits_response.status_code != 200:
            return jsonify({'error': f'GitHub API error: {commits_response.status_code}', 'details': commits_response.text}), 400
        
        commits = commits_response.json()
        
        return jsonify(commits), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_details_bp.route('/<repo_id>/github/issues', methods=['GET'])
@limiter.limit("50/minute")
def get_github_issues(repo_id):
    """Get GitHub issues for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Check if repo_url is a GitHub URL
    repo_url = repository.get('repo_url', '')
    if 'github.com' not in repo_url:
        return jsonify({'error': 'Not a GitHub repository', 'url': repo_url}), 400
    
    # Extract owner and repo name
    try:
        # Handle both HTTPS and SSH URLs
        owner = None
        repo_name = None
        
        if repo_url.startswith('git@github.com:'):
            # SSH format
            parts = repo_url.replace('git@github.com:', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1].replace('.git', '')
        else:
            # HTTPS format
            parts = repo_url.strip('/').split('/')
            if len(parts) >= 4 and parts[-3] == 'github.com':
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
        
        if not owner or not repo_name:
            return jsonify({'error': 'Could not parse GitHub repository URL'}), 400
        
        # Get GitHub token from environment variable
        github_token = os.environ.get('GITHUB_TOKEN', '')
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Fetch issues directly from GitHub API
        issues_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/issues?state=all&per_page=10',
            headers=headers
        )
        
        if issues_response.status_code != 200:
            return jsonify({'error': f'GitHub API error: {issues_response.status_code}', 'details': issues_response.text}), 400
        
        issues = issues_response.json()
        
        # Filter out pull requests (GitHub API includes PRs in issues endpoint)
        issues = [issue for issue in issues if 'pull_request' not in issue]
        
        return jsonify(issues), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_details_bp.route('/<repo_id>/github/pulls', methods=['GET'])
@limiter.limit("50/minute")
def get_github_pulls(repo_id):
    """Get GitHub pull requests for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Check if repo_url is a GitHub URL
    repo_url = repository.get('repo_url', '')
    if 'github.com' not in repo_url:
        return jsonify({'error': 'Not a GitHub repository', 'url': repo_url}), 400
    
    # Extract owner and repo name
    try:
        # Handle both HTTPS and SSH URLs
        owner = None
        repo_name = None
        
        if repo_url.startswith('git@github.com:'):
            # SSH format
            parts = repo_url.replace('git@github.com:', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1].replace('.git', '')
        else:
            # HTTPS format
            parts = repo_url.strip('/').split('/')
            if len(parts) >= 4 and parts[-3] == 'github.com':
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
        
        if not owner or not repo_name:
            return jsonify({'error': 'Could not parse GitHub repository URL'}), 400
        
        # Get GitHub token from environment variable
        github_token = os.environ.get('GITHUB_TOKEN', '')
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Fetch pull requests directly from GitHub API
        pulls_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/pulls?state=all&per_page=10',
            headers=headers
        )
        
        if pulls_response.status_code != 200:
            return jsonify({'error': f'GitHub API error: {pulls_response.status_code}', 'details': pulls_response.text}), 400
        
        pulls = pulls_response.json()
        
        return jsonify(pulls), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@repo_details_bp.route('/<repo_id>/github/languages', methods=['GET'])
@limiter.limit("50/minute")
def get_github_languages(repo_id):
    """Get GitHub languages for a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Check if repo_url is a GitHub URL
    repo_url = repository.get('repo_url', '')
    if 'github.com' not in repo_url:
        return jsonify({'error': 'Not a GitHub repository', 'url': repo_url}), 400
    
    # Extract owner and repo name
    try:
        # Handle both HTTPS and SSH URLs
        owner = None
        repo_name = None
        
        if repo_url.startswith('git@github.com:'):
            # SSH format
            parts = repo_url.replace('git@github.com:', '').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1].replace('.git', '')
        else:
            # HTTPS format
            parts = repo_url.strip('/').split('/')
            if len(parts) >= 4 and parts[-3] == 'github.com':
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
        
        if not owner or not repo_name:
            return jsonify({'error': 'Could not parse GitHub repository URL'}), 400
        
        # Get GitHub token from environment variable
        github_token = os.environ.get('GITHUB_TOKEN', '')
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Fetch languages directly from GitHub API
        languages_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/languages',
            headers=headers
        )
        
        if languages_response.status_code != 200:
            return jsonify({'error': f'GitHub API error: {languages_response.status_code}', 'details': languages_response.text}), 400
        
        languages = languages_response.json()
        
        return jsonify(languages), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 