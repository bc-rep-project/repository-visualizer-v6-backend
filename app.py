import os
import subprocess
import shutil
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from scripts.data_processor import convert_files_to_json
from datetime import datetime

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://repository-visualizer-v6-frontend.vercel.app",
            "http://localhost:3000"  # For local development
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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

def check_git_available():
    """Check if git is available in the system."""
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

@app.route('/')
def health_check():
    """Health check endpoint for Render."""
    git_available = check_git_available()
    return jsonify({
        'status': 'healthy',
        'message': 'Repository Visualization API is running',
        'git_available': git_available
    }), 200

def stream_clone_output(process, repo_id):
    """Stream clone progress and update global progress tracker."""
    try:
        while True:
            # Read from stderr instead of stdout since git sends progress to stderr
            output = process.stderr.readline()
            if not output and process.poll() is not None:
                break
            if output:
                try:
                    # Handle both string and bytes output
                    if isinstance(output, bytes):
                        progress_msg = output.decode('utf-8').strip()
                    else:
                        progress_msg = output.strip()
                    clone_progress[repo_id] = progress_msg
                except Exception as e:
                    clone_progress[repo_id] = f"Processing output: {str(output)}"
        
        return_code = process.poll()
        if return_code == 0:
            clone_progress[repo_id] = "Clone completed successfully"
        else:
            clone_progress[repo_id] = f"Process exited with code {return_code}"
        return return_code
    except Exception as e:
        clone_progress[repo_id] = f"Error in stream handling: {str(e)}"
        return 1

@app.route('/clone', methods=['POST'])
@limiter.limit("10 per minute")
def clone_repo():
    # Check if git is available
    if not check_git_available():
        return jsonify({'error': 'Git is not available on the server'}), 500

    # Validate request
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    repo_url = request.json.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
        
    # Validate repository URL format
    if not repo_url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid repository URL format'}), 400

    try:
        # Extract username/repo from the URL
        if 'github.com/' not in repo_url:
            return jsonify({'error': 'Only GitHub repositories are supported'}), 400
            
        repo_name = repo_url.split('github.com/')[1].replace('.git', '')
        repo_path = os.path.join(app.config['REPO_DIR'], repo_name)
        repo_id = repo_name.replace('/', '_')
        
        # Initialize progress tracking
        clone_progress[repo_id] = 'Starting clone operation...'
        
        # Create the repos directory if it doesn't exist
        try:
            os.makedirs(app.config['REPO_DIR'], exist_ok=True)
        except Exception as e:
            return jsonify({'error': f'Failed to create repository directory: {str(e)}'}), 500
        
        # If repo exists, remove it for fresh clone
        if os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path)
            except Exception as e:
                return jsonify({'error': f'Failed to clean existing repository: {str(e)}'}), 500
        
        # Clone the repository with progress tracking
        try:
            process = subprocess.Popen(
                ['git', 'clone', '--progress', repo_url, repo_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr for progress
                universal_newlines=False  # Keep as bytes to handle properly
            )
        except Exception as e:
            return jsonify({'error': f'Failed to start git clone: {str(e)}'}), 500
        
        # Stream and track progress
        return_code = stream_clone_output(process, repo_id)
        
        if return_code != 0:
            error_msg = clone_progress.get(repo_id, 'Unknown error during clone')
            return jsonify({'error': f'Clone operation failed: {error_msg}'}), 500
        
        # Verify the repository was cloned successfully
        if not os.path.exists(os.path.join(repo_path, '.git')):
            return jsonify({'error': 'Repository appears to be empty or invalid'}), 500
        
        return jsonify({
            'message': 'Repository cloned successfully',
            'repo_path': repo_path,
            'repo_id': repo_id
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        if 'repo_id' in locals():
            clone_progress[repo_id] = f'Error: {error_msg}'
        return jsonify({
            'error': error_msg,
            'details': 'An unexpected error occurred during the clone operation'
        }), 500

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
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)