import os
import subprocess
import shutil
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from scripts.data_processor import convert_files_to_json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=os.environ.get('REDIS_URL', 'memory://'),
    storage_options={"socket_connect_timeout": 30} if os.environ.get('REDIS_URL') else {},
    default_limits=["200 per day", "50 per hour"]
)

# Define the directory where repositories will be cloned
app.config['REPO_DIR'] = os.path.join(os.getcwd(), 'repos')

# Global variables
clone_progress = {}
repo_metadata = {}

@app.route('/')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'message': 'Repository Visualization API is running'
    }), 200

def stream_clone_output(process, repo_id):
    """Stream clone progress and update global progress tracker."""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            progress_msg = output.strip().decode('utf-8')
            clone_progress[repo_id] = progress_msg
    return process.poll()

@app.route('/clone', methods=['POST'])
@limiter.limit("10 per minute")
def clone_repo():
    repo_url = request.json.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
        
    # Validate repository URL format
    if not repo_url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid repository URL format'}), 400

    try:
        # Extract username/repo from the URL
        repo_name = repo_url.split('github.com/')[1].replace('.git', '')
        repo_path = os.path.join(app.config['REPO_DIR'], repo_name)
        repo_id = repo_name.replace('/', '_')
        
        # Initialize progress tracking
        clone_progress[repo_id] = 'Starting clone operation...'
        
        # Create the repos directory if it doesn't exist
        os.makedirs(app.config['REPO_DIR'], exist_ok=True)
        
        # If repo exists, remove it for fresh clone
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        # Clone the repository with progress tracking
        process = subprocess.Popen(
            ['git', 'clone', '--progress', repo_url, repo_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Stream and track progress
        return_code = stream_clone_output(process, repo_id)
        
        if return_code != 0:
            raise Exception('Clone operation failed')
        
        clone_progress[repo_id] = 'Clone completed successfully'
        return jsonify({
            'message': 'Repository cloned successfully',
            'repo_path': repo_path,
            'repo_id': repo_id
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        if repo_id in clone_progress:
            clone_progress[repo_id] = f'Error: {error_msg}'
        return jsonify({'error': error_msg}), 500

@app.route('/progress/<repo_id>', methods=['GET'])
def get_progress(repo_id):
    """Get the current progress of a clone operation."""
    return jsonify({
        'progress': clone_progress.get(repo_id, 'No progress information available')
    })

@app.route('/convert', methods=['POST'])
def convert_repo():
    repo_path = request.json.get('repo_path')
    if not repo_path or not os.path.exists(repo_path):
        return jsonify({'error': 'Invalid or missing repository path'}), 400
    
    try:
        json_file_path = convert_files_to_json(repo_path)
        
        # Read the generated JSON to include in response
        with open(json_file_path, 'r') as f:
            analysis_data = json.load(f)
        
        return jsonify({
            'message': 'Files converted successfully',
            'json_path': json_file_path,
            'analysis': analysis_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to convert files',
            'details': str(e)
        }), 500

@app.route('/repositories', methods=['GET'])
def list_repositories():
    """List all cloned repositories and their metadata."""
    try:
        repos = []
        if os.path.exists(app.config['REPO_DIR']):
            for repo_name in os.listdir(app.config['REPO_DIR']):
                repo_path = os.path.join(app.config['REPO_DIR'], repo_name)
                if os.path.isdir(repo_path):
                    repo_info = repo_metadata.get(repo_name, {
                        'name': repo_name,
                        'cloned_at': datetime.fromtimestamp(os.path.getctime(repo_path)).isoformat(),
                        'status': 'cloned'
                    })
                    repos.append(repo_info)
        return jsonify({'repositories': repos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/repository/<repo_id>', methods=['GET'])
def get_repository(repo_id):
    """Get detailed information about a specific repository."""
    try:
        repo_path = os.path.join(app.config['REPO_DIR'], repo_id.replace('_', '/'))
        if not os.path.exists(repo_path):
            return jsonify({'error': 'Repository not found'}), 404

        # Get repository statistics
        file_count = sum([len(files) for _, _, files in os.walk(repo_path)])
        size = sum(os.path.getsize(os.path.join(dirpath, filename))
                  for dirpath, _, filenames in os.walk(repo_path)
                  for filename in filenames)

        repo_info = {
            'id': repo_id,
            'path': repo_path,
            'file_count': file_count,
            'size_bytes': size,
            'cloned_at': datetime.fromtimestamp(os.path.getctime(repo_path)).isoformat(),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(repo_path)).isoformat(),
            'status': clone_progress.get(repo_id, 'completed')
        }
        return jsonify(repo_info), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/repository/<repo_id>', methods=['DELETE'])
def delete_repository(repo_id):
    """Delete a repository from the system."""
    try:
        repo_path = os.path.join(app.config['REPO_DIR'], repo_id.replace('_', '/'))
        if not os.path.exists(repo_path):
            return jsonify({'error': 'Repository not found'}), 404

        shutil.rmtree(repo_path)
        if repo_id in clone_progress:
            del clone_progress[repo_id]
        if repo_id in repo_metadata:
            del repo_metadata[repo_id]

        return jsonify({'message': f'Repository {repo_id} deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)