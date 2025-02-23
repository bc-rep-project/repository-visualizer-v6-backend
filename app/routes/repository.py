from flask import Blueprint, jsonify, request
from ..services.repository_service import RepositoryService
from .. import limiter

repo_bp = Blueprint('repository', __name__, url_prefix='/api/repositories')

@repo_bp.route('/', methods=['GET'])
def list_repositories():
    """List all repositories."""
    repositories = RepositoryService.get_all_repositories()
    return jsonify({
        'repositories': [repo.to_dict() for repo in repositories]
    }), 200

@repo_bp.route('/', methods=['POST'])
@limiter.limit("10 per minute")
def clone_repository():
    """Clone a new repository."""
    if not RepositoryService.check_git_available():
        return jsonify({'error': 'Git is not available on the server'}), 500

    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    repo_url = request.json.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400

    if not repo_url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid repository URL format'}), 400

    if 'github.com/' not in repo_url:
        return jsonify({'error': 'Only GitHub repositories are supported'}), 400

    try:
        repo_name = repo_url.split('github.com/')[1].replace('.git', '')
        repo_path = f"repos/{repo_name}"
        repo_id = repo_name.replace('/', '_')

        # Create repository record
        repo = RepositoryService.create_repository(repo_url, repo_path, repo_id)

        # Clone repository
        success, message = RepositoryService.clone_repository(repo_url, repo_path, repo_id)
        
        if success:
            # Update repository stats
            stats = RepositoryService.get_repository_stats(repo_path)
            repo = RepositoryService.update_repository_status(repo, 'completed', stats)
            return jsonify(repo.to_dict()), 200
        else:
            repo = RepositoryService.update_repository_status(repo, 'failed')
            return jsonify({'error': message}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_bp.route('/<repo_id>', methods=['GET'])
def get_repository(repo_id):
    """Get repository details."""
    repo = RepositoryService.get_repository(repo_id)
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404
    return jsonify(repo.to_dict()), 200

@repo_bp.route('/<repo_id>', methods=['DELETE'])
def delete_repository(repo_id):
    """Delete a repository."""
    repo = RepositoryService.get_repository(repo_id)
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404

    if RepositoryService.delete_repository(repo):
        return jsonify({'message': 'Repository deleted successfully'}), 200
    else:
        return jsonify({'error': 'Failed to delete repository'}), 500 