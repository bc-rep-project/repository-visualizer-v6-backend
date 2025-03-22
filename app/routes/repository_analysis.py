from flask import Blueprint, jsonify, request
from app.services.repository_service import RepositoryService
from app import limiter, mongo
from datetime import datetime
import os

repo_analysis_bp = Blueprint('repository_analysis', __name__, url_prefix='/api/repositories')

@repo_analysis_bp.route('/<repo_id>/structure', methods=['GET'])
@limiter.limit("30/minute")
def get_repository_structure(repo_id):
    """Get the file structure of a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Get repository path
    repo_path = repository.get('repo_path')
    if not repo_path or not os.path.exists(repo_path):
        return jsonify({'error': 'Repository directory not found'}), 404
    
    # Build file tree
    file_tree = {
        'name': os.path.basename(repo_path),
        'path': '',
        'type': 'directory',
        'children': []
    }
    
    RepositoryService._build_file_tree(repo_path, file_tree['children'], '')
    
    return jsonify({'structure': file_tree}), 200

@repo_analysis_bp.route('/<repo_id>/dependencies', methods=['GET'])
@limiter.limit("30/minute")
def get_repository_dependencies(repo_id):
    """Get the dependencies between files in a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    # Get repository analysis which includes dependencies
    analysis = RepositoryService.analyze_repository_code(repo_id)
    if 'error' in analysis:
        return jsonify({'error': analysis['error']}), 404
    
    # Extract dependencies from the analysis
    dependencies = []
    if 'graph' in analysis and 'edges' in analysis['graph']:
        dependencies = analysis['graph']['edges']
    
    return jsonify({'dependencies': dependencies}), 200

@repo_analysis_bp.route('/<repo_id>/functions', methods=['GET'])
@limiter.limit("30/minute")
def get_repository_functions(repo_id):
    """Get the functions defined in a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    # Get repository analysis
    analysis = RepositoryService.analyze_repository_code(repo_id)
    if 'error' in analysis:
        return jsonify({'error': analysis['error']}), 404
    
    # Extract functions from the analysis
    functions = []
    if 'graph' in analysis and 'nodes' in analysis['graph']:
        # Filter nodes to only include functions and methods
        functions = [
            node for node in analysis['graph']['nodes'] 
            if node.get('type') in ['function', 'method']
        ]
    
    # Apply optional filters
    file_filter = request.args.get('file')
    language_filter = request.args.get('language')
    
    if file_filter:
        functions = [f for f in functions if file_filter in f.get('path', '')]
    
    if language_filter:
        functions = [f for f in functions if f.get('language') == language_filter]
    
    return jsonify({'functions': functions}), 200

@repo_analysis_bp.route('/<repo_id>/languages', methods=['GET'])
@limiter.limit("30/minute")
def get_repository_languages(repo_id):
    """Get statistics about languages used in a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Get languages from repository
    languages = repository.get('languages', {})
    
    # Calculate total bytes
    total_bytes = repository.get('total_size', 0)
    
    return jsonify({
        'languages': languages,
        'total_bytes': total_bytes
    }), 200

@repo_analysis_bp.route('/<repo_id>/files', methods=['GET'])
@limiter.limit("50/minute")
def get_file_content(repo_id):
    """Get the content of a specific file in a repository."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Get file path from query parameters
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400
    
    # Get repository path
    repo_path = repository.get('repo_path')
    if not repo_path or not os.path.exists(repo_path):
        return jsonify({'error': 'Repository directory not found'}), 404
    
    # Construct absolute file path
    absolute_file_path = os.path.join(repo_path, file_path.lstrip('/'))
    
    # Check if file exists
    if not os.path.isfile(absolute_file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Get file size
    size = os.path.getsize(absolute_file_path)
    
    # Check if file is too large (limit to 1MB for text files)
    if size > 1024 * 1024:  # 1MB
        return jsonify({'error': 'File is too large to display'}), 413
    
    # Determine file language based on extension
    _, ext = os.path.splitext(file_path)
    language = RepositoryService._get_language_from_extension(ext)
    
    # Check if file is binary (common binary extensions)
    binary_extensions = ['.exe', '.dll', '.so', '.bin', '.dat', '.jpg', '.jpeg', '.png', '.gif', '.ico', 
                          '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.tar', '.gz', '.rar']
    if ext.lower() in binary_extensions:
        return jsonify({
            'file': {
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': size,
                'language': language,
                'is_binary': True,
                'content': f"Binary file: {os.path.basename(file_path)} ({size} bytes)"
            }
        }), 200
    
    # Read file content
    try:
        # Try to detect if the file is binary by reading the first few bytes
        is_binary = False
        with open(absolute_file_path, 'rb') as f:
            sample = f.read(1024)
            if b'\x00' in sample:  # Null bytes typically indicate binary data
                is_binary = True
        
        if is_binary:
            return jsonify({
                'file': {
                    'name': os.path.basename(file_path),
                    'path': file_path,
                    'size': size,
                    'language': language,
                    'is_binary': True,
                    'content': f"Binary file: {os.path.basename(file_path)} ({size} bytes)"
                }
            }), 200
        
        # Read the file as text
        with open(absolute_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'file': {
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': size,
                'language': language,
                'is_binary': False,
                'content': content
            }
        }), 200
    except UnicodeDecodeError:
        # Handle case where file cannot be decoded as UTF-8 (likely binary)
        return jsonify({
            'file': {
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': size,
                'language': language,
                'is_binary': True,
                'content': f"Binary file: {os.path.basename(file_path)} ({size} bytes)"
            }
        }), 200

@repo_analysis_bp.route('/<repo_id>/analysis/save', methods=['POST'])
@limiter.limit("10/minute")
def save_repository_analysis(repo_id):
    """Save repository analysis to MongoDB."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Get analysis data from request body
    analysis_data = request.json
    if not analysis_data:
        # If no data provided, perform analysis
        analysis_data = RepositoryService.analyze_repository_code(repo_id)
    
    # Save analysis to MongoDB
    mongo.repository_analyses.update_one(
        {'repository_id': repo_id},
        {'$set': {
            'repository_id': repo_id,
            'analysis': analysis_data,
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'last_manual_save': datetime.utcnow().isoformat() + 'Z'
        }},
        upsert=True
    )
    
    return jsonify({
        'message': 'Repository analysis saved successfully',
        'repository_id': repo_id
    }), 200 