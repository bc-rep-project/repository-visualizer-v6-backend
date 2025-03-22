from flask import Blueprint, jsonify, request
from app.services.repository_service import RepositoryService
from app.services.enhanced_repository_service import EnhancedRepositoryService
from bson import ObjectId
from app import limiter, mongo
from flask_pymongo import PyMongo
from datetime import datetime
import os

repo_bp = Blueprint('repositories', __name__, url_prefix='')

@repo_bp.route('/api/repositories', methods=['GET'])
@limiter.limit("30 per minute")
def get_repositories():
    """Get all repositories with optional filtering."""
    try:
        # Get pagination parameters
        page = request.args.get('page', '1')
        limit = request.args.get('limit', '10')
        sort_by = request.args.get('sort', 'created_at')
        sort_dir = request.args.get('dir', 'desc')
        
        # Get filter parameters
        status = request.args.get('status', 'All Status')
        language = request.args.get('language', 'All Languages')
        size_range = request.args.get('size', 'Size Range')
        search = request.args.get('search', '')
        
        # Parse size range if provided
        size_min = 0
        size_max = float('inf')
        if size_range != 'Size Range':
            if '<' in size_range:
                # Less than X MB
                size_max = float(size_range.replace('< ', '').replace(' MB', ''))
            elif '>' in size_range:
                # Greater than X MB
                size_min = float(size_range.replace('> ', '').replace(' MB', ''))
            elif '-' in size_range:
                # Range X-Y MB
                parts = size_range.replace(' MB', '').split('-')
                size_min = float(parts[0])
                size_max = float(parts[1])
        
        # Convert page and limit to integers
        try:
            page = int(page)
            limit = int(limit)
            
            # Ensure minimum values
            page = max(1, page)
            limit = max(1, min(100, limit))  # Limit between 1 and 100
        except ValueError:
            page = 1
            limit = 10
        
        # Print debug info
        print("DEBUG: Request parameters:")
        print(f"page: {page}, limit: {limit}, sort_by: {sort_by}, sort_dir: {sort_dir}")
        print(f"status: {status}, language: {language}, size_range: {size_range}, search: {search}")
        
        # Create filter dictionary
        filters = {
            'status': status,
            'language': language,
            'size_min': size_min,
            'size_max': size_max,
            'search': search
        }
        
        print(f"DEBUG: Filter dictionary: {filters}")
        
        # Debug: Direct MongoDB query for language
        if language and language != 'All Languages':
            print(f"DEBUG: Direct MongoDB query for language '{language}'")
            
            # Test with dot prefix
            dot_query = {f'languages..{language}': {'$exists': True}}
            dot_count = mongo.repositories.count_documents(dot_query)
            print(f"Query with dot prefix: {dot_query}")
            print(f"Result count: {dot_count}")
            
            # Test without dot prefix
            no_dot_query = {f'languages.{language}': {'$exists': True}}
            no_dot_count = mongo.repositories.count_documents(no_dot_query)
            print(f"Query without dot prefix: {no_dot_query}")
            print(f"Result count: {no_dot_count}")
            
            # Check each repository's languages
            print("Checking each repository's languages:")
            for repo in mongo.repositories.find():
                repo_name = repo.get('repo_name', 'Unknown')
                languages = repo.get('languages', {})
                print(f"Repository: {repo_name}")
                print(f"Languages: {languages}")
                
                # Check if language exists with dot prefix
                dot_key = f'.{language}'
                if dot_key in languages:
                    print(f"Language '{dot_key}' found with dot prefix")
                
                # Check if language exists without dot prefix
                if language in languages:
                    print(f"Language '{language}' found without dot prefix")
        
        # Get repositories with pagination and filters
        result = RepositoryService.get_repositories(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
            filters=filters
        )
        
        # Return result
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting repositories: {e}")
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
    languages = RepositoryService.get_all_languages()
    return jsonify(languages), 200

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

@repo_bp.route('/api/repositories/update-dates', methods=['POST'])
@limiter.limit("5 per minute")
def update_repository_dates():
    """Update all repository dates to ISO format for consistent sorting."""
    try:
        import re
        
        # Find all repositories
        repositories = mongo.repositories.find({})
        
        update_count = 0
        
        for repo in repositories:
            repo_id = repo['_id']
            created_at = repo.get('created_at')
            updated_at = repo.get('updated_at')
            
            updates = {}
            
            # Check if created_at is not in ISO format
            if created_at and not created_at.endswith('Z'):
                try:
                    # Parse the date from the format: Tue, 18 Mar 2025 20:26:14 GMT
                    if isinstance(created_at, str) and re.match(r'[A-Za-z]+, \d+ [A-Za-z]+ \d+ \d+:\d+:\d+ GMT', created_at):
                        date = datetime.strptime(created_at, '%a, %d %b %Y %H:%M:%S GMT')
                        iso_date = date.isoformat() + 'Z'
                        updates['created_at'] = iso_date
                    else:
                        # Fall back to current time if parsing fails
                        updates['created_at'] = datetime.utcnow().isoformat() + 'Z'
                except Exception:
                    # If parsing fails, set to current time
                    updates['created_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Check if updated_at is not in ISO format
            if updated_at and not updated_at.endswith('Z'):
                try:
                    # Parse the date from the format: Tue, 18 Mar 2025 20:26:14 GMT
                    if isinstance(updated_at, str) and re.match(r'[A-Za-z]+, \d+ [A-Za-z]+ \d+ \d+:\d+:\d+ GMT', updated_at):
                        date = datetime.strptime(updated_at, '%a, %d %b %Y %H:%M:%S GMT')
                        iso_date = date.isoformat() + 'Z'
                        updates['updated_at'] = iso_date
                    else:
                        # Fall back to current time if parsing fails
                        updates['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                except Exception:
                    # If parsing fails, set to current time
                    updates['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Apply updates if needed
            if updates:
                mongo.repositories.update_one(
                    {'_id': repo_id},
                    {'$set': updates}
                )
                update_count += 1
        
        return jsonify({
            'message': f'Updated dates for {update_count} repositories to ISO format',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@repo_bp.route('/api/repositories/<repo_id>/enhanced/save', methods=['POST'])
@limiter.limit("10/minute")
def save_enhanced_repository_analysis(repo_id):
    """Save enhanced repository analysis to MongoDB."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Get enhanced analysis data from request body
    enhanced_data = request.json
    if not enhanced_data:
        # If no data provided, try to get it from EnhancedRepositoryService
        try:
            from app.services.enhanced_repository_service import EnhancedRepositoryService
            print(f"Generating enhanced analysis for repository {repo_id}")
            enhanced_data = EnhancedRepositoryService.analyze_repository_code(repo_id)
            if not enhanced_data:
                return jsonify({'error': 'Failed to generate enhanced analysis: No data returned'}), 500
            print(f"Successfully generated enhanced analysis for repository {repo_id}")
        except ImportError as e:
            print(f"Error importing EnhancedRepositoryService: {e}")
            return jsonify({'error': 'Enhanced repository service is not available'}), 500
        except Exception as e:
            print(f"Error generating enhanced analysis: {e}")
            return jsonify({'error': f'Failed to generate enhanced analysis: {str(e)}'}), 500
    
    try:
        # Save enhanced analysis to MongoDB
        mongo.enhanced_repository_analyses.update_one(
            {'repository_id': repo_id},
            {'$set': {
                'repository_id': repo_id,
                'enhanced_analysis': enhanced_data,
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'last_manual_save': datetime.utcnow().isoformat() + 'Z'
            }},
            upsert=True
        )
        
        return jsonify({
            'message': 'Enhanced repository analysis saved successfully',
            'repository_id': repo_id
        }), 200
    except Exception as e:
        print(f"Error saving enhanced analysis to MongoDB: {e}")
        return jsonify({'error': f'Failed to save enhanced analysis: {str(e)}'}), 500

@repo_bp.route('/api/repositories/<repo_id>/save', methods=['POST'])
@limiter.limit("20/minute")
def save_repository(repo_id):
    """Save repository data to MongoDB."""
    if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
        return jsonify({'error': f'Invalid repository ID: {repo_id}'}), 400
        
    repository = RepositoryService.get_repository(repo_id)
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    repo_path = repository.get('repo_path')
    if not repo_path or not os.path.exists(repo_path):
        return jsonify({'error': 'Repository directory not found'}), 404
    
    try:
        # Get latest stats
        stats = RepositoryService._get_repository_stats(repo_path)
        
        # Update repository with latest stats
        mongo.repositories.update_one(
            {'_id': ObjectId(repo_id)},
            {'$set': {
                'file_count': stats['file_count'],
                'directory_count': stats['directory_count'],
                'total_size': stats['total_size'],
                'languages': stats['languages'],
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'last_manual_save': datetime.utcnow().isoformat() + 'Z'
            }}
        )
        
        # Get updated repository
        updated_repo = RepositoryService.get_repository(repo_id)
        
        return jsonify({
            'message': 'Repository saved successfully',
            'repository': updated_repo
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to save repository: {str(e)}'}), 500