from flask import Blueprint, jsonify, request
from app.services.repository_service import RepositoryService
from app import limiter
import os
import re

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

@repo_analysis_bp.route('/<repo_id>/function-content', methods=['GET'])
@limiter.limit("100/minute")
def get_function_class_content(repo_id):
    """Get the content of a specific function or class from a file."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Get parameters from query
    file_path = request.args.get('path')
    name = request.args.get('name')
    type_of_content = request.args.get('type', 'function')  # 'function', 'class', or 'method'
    
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400
    
    if not name:
        return jsonify({'error': 'Function or class name is required'}), 400
    
    # Get repository path
    repo_path = repository.get('repo_path')
    if not repo_path or not os.path.exists(repo_path):
        return jsonify({'error': 'Repository directory not found'}), 404
    
    # Construct absolute file path
    absolute_file_path = os.path.join(repo_path, file_path.lstrip('/'))
    
    # Check if file exists
    if not os.path.isfile(absolute_file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Read the file content
        with open(absolute_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Determine file language based on extension
        _, ext = os.path.splitext(file_path)
        language = RepositoryService._get_language_from_extension(ext)
        
        # Extract the function or class content based on its name and type
        extracted_content = ''
        line_start = 0
        line_end = 0
        
        if type_of_content in ['function', 'method']:
            # Match function or method definition patterns for different languages
            patterns = []
            if language == 'javascript' or language == 'typescript':
                # JavaScript/TypeScript patterns
                patterns = [
                    # Function declaration
                    rf'(?:export\s+)?(?:async\s+)?function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{[\s\S]*?\}}',
                    # Function expression
                    rf'(?:export\s+)?const\s+{re.escape(name)}\s*=\s*(?:async\s+)?function\s*\([^)]*\)\s*\{{[\s\S]*?\}}',
                    # Arrow function
                    rf'(?:export\s+)?const\s+{re.escape(name)}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{{[\s\S]*?\}}',
                    # Method in a class
                    rf'(?:async\s+)?{re.escape(name)}\s*\([^)]*\)\s*\{{[\s\S]*?\}}'
                ]
            elif language == 'python':
                # Python function pattern
                patterns = [
                    rf'def\s+{re.escape(name)}\s*\([^)]*\):[^\n]*(?:\n(?:[ \t]+[^\n]*)?)*'
                ]
            elif language == 'java':
                # Java method pattern
                patterns = [
                    rf'(?:public|private|protected)?\s+(?:static\s+)?[\w<>[\]]+\s+{re.escape(name)}\s*\([^)]*\)\s*\{{[\s\S]*?\}}'
                ]
        
        elif type_of_content == 'class':
            # Match class definition patterns for different languages
            if language == 'javascript' or language == 'typescript':
                # JavaScript/TypeScript class pattern
                patterns = [
                    rf'(?:export\s+)?class\s+{re.escape(name)}\s*(?:extends\s+\w+)?\s*\{{[\s\S]*?\}}'
                ]
            elif language == 'python':
                # Python class pattern
                patterns = [
                    rf'class\s+{re.escape(name)}[^\n]*:[^\n]*(?:\n(?:[ \t]+[^\n]*)?)*'
                ]
            elif language == 'java':
                # Java class pattern
                patterns = [
                    rf'(?:public|private|protected)?\s*class\s+{re.escape(name)}\s*(?:extends\s+\w+)?\s*(?:implements\s+[^{{]+)?\s*\{{[\s\S]*?\}}'
                ]
        
        # Try each pattern to find the function or class
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                extracted_content = match.group(0)
                # Calculate line numbers
                content_before = content[:match.start()]
                line_start = content_before.count('\n') + 1
                line_end = line_start + extracted_content.count('\n')
                break
            if extracted_content:
                break
        
        if not extracted_content:
            return jsonify({
                'error': f'{type_of_content.capitalize()} {name} not found in file'
            }), 404
        
        return jsonify({
            'content': extracted_content,
            'line_start': line_start,
            'line_end': line_end,
            'language': language,
            'name': name,
            'type': type_of_content,
            'file_path': file_path
        }), 200
        
    except UnicodeDecodeError:
        return jsonify({
            'error': 'File cannot be decoded as text'
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Error extracting {type_of_content}: {str(e)}'
        }), 500 