from flask import Blueprint, jsonify, request
from app.services.repository_service import RepositoryService
from app.services.enhanced_repository_service import EnhancedRepositoryService
from app import limiter

repo_bp = Blueprint('repositories', __name__, url_prefix='')

@repo_bp.route('/api/repositories', methods=['GET'])
@limiter.limit("30 per minute")
def get_repositories():
    """Get all repositories."""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 10, type=int), 50)  # Cap at 50
        sort_by = request.args.get('sort', 'created_at')
        sort_dir = request.args.get('dir', 'desc')
        
        # Get repositories
        repositories = RepositoryService.get_repositories(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        
        return jsonify(repositories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@repo_bp.route('/api/repositories', methods=['POST'])
@limiter.limit("20/minute")
def add_repository():
    """Add a new repository."""
    data = request.get_json()
    
    if not data or 'repo_url' not in data:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    repo_url = data['repo_url']
    
    # Validate repository URL
    if not repo_url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid repository URL format'}), 400
    
    # Add repository
    repository = RepositoryService.add_repository(repo_url)
    
    return jsonify(repository), 201

@repo_bp.route('/api/repositories/<repo_id>', methods=['GET'])
@limiter.limit("100/minute")
def get_repository(repo_id):
    """Get a repository by ID."""
    repository = RepositoryService.get_repository(repo_id)
    
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    return jsonify(repository), 200

@repo_bp.route('/api/repositories/<repo_id>', methods=['DELETE'])
@limiter.limit("20/minute")
def delete_repository(repo_id):
    # Special case for "None" ID
    if repo_id == "None":
        success = RepositoryService.delete_repository("None")
        if not success:
            return jsonify({'error': 'Repository not found or could not be deleted'}), 404
        return '', 204
        
    # Normal case
    success = RepositoryService.delete_repository(repo_id)
    if not success:
        return jsonify({'error': 'Repository not found'}), 404
    return '', 204

@repo_bp.route('/api/repositories/<repo_id>/analyze', methods=['GET'])
@limiter.limit("10/minute")
def analyze_repository(repo_id):
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
    
    try:
        # Log the request
        print(f"Analyzing repository with ID: {repo_id}")
        
        # Get the analysis using the enhanced service
        analysis = EnhancedRepositoryService.analyze_repository_code(repo_id)
        
        # Check for errors
        if 'error' in analysis:
            print(f"Error analyzing repository {repo_id}: {analysis['error']}")
            return jsonify({'error': analysis['error']}), 404
        
        # Log success
        print(f"Successfully analyzed repository {repo_id}")
        
        return jsonify(analysis), 200
    except Exception as e:
        print(f"Exception analyzing repository {repo_id}: {str(e)}")
        return jsonify({'error': f'Failed to analyze repository: {str(e)}'}), 500

@repo_bp.route('/api/repositories/languages', methods=['GET'])
@limiter.limit("50/minute")
def get_languages():
    """Get all languages used across repositories."""
    try:
        languages = RepositoryService.get_all_languages()
        return jsonify(languages), 200
    except Exception as e:
        import traceback
        print(f"Error fetching languages: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to retrieve languages: {str(e)}'}), 500

@repo_bp.route('/api/repositories/<repo_id>/analyze/debug', methods=['GET'])
@limiter.limit("10/minute")
def debug_repository_analysis(repo_id):
    """Debug endpoint to see raw analysis data structure."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
    
    try:
        # Get the analysis
        analysis = RepositoryService.analyze_repository_code(repo_id)
        
        # Add debug information
        debug_info = {
            'has_tree': 'tree' in analysis,
            'tree_type': type(analysis.get('tree')).__name__,
            'tree_children_count': len(analysis.get('tree', {}).get('children', [])),
            'has_graph': 'graph' in analysis,
            'nodes_count': len(analysis.get('graph', {}).get('nodes', [])),
            'edges_count': len(analysis.get('graph', {}).get('edges', [])),
            'sample_node': analysis.get('graph', {}).get('nodes', [{}])[0] if analysis.get('graph', {}).get('nodes') else None,
            'sample_edge': analysis.get('graph', {}).get('edges', [{}])[0] if analysis.get('graph', {}).get('edges') else None,
        }
        
        return jsonify({
            'debug_info': debug_info,
            'analysis': analysis
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to analyze repository: {str(e)}'}), 500