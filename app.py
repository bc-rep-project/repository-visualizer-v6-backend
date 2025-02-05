import os
import subprocess
import shutil
import json
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from scripts.data_processor import convert_files_to_json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# Define the directory where repositories will be cloned
app.config['REPO_DIR'] = os.path.join(os.getcwd(), 'repos')

# Global variable to store clone progress
clone_progress = {}

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
def clone_repo():
    repo_url = request.json.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400

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

if __name__ == '__main__':
    app.run(debug=True)