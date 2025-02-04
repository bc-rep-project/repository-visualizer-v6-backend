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

@app.route('/clone', methods=['POST'])
def clone_repo():
    repo_url = request.json.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400

    # Extract username/repo from the URL
    try:
        repo_name = repo_url.split('github.com/')[1].replace('.git', '')
        repo_path = os.path.join(app.config['REPO_DIR'], repo_name)
    except IndexError:
        return jsonify({'error': 'Invalid repository URL format'}), 400
    
    # check if repo exists and delete
    if os.path.exists(repo_path):
        return jsonify({'message': 'Repository already cloned, initiating file conversion', 'repo_path': repo_path}), 200
        #shutil.rmtree(repo_path)

    # Create the repos directory if it doesn't exist
    os.makedirs(app.config['REPO_DIR'], exist_ok=True)

    # Clone the repository using a subprocess call, capturing output and errors
    process = subprocess.Popen(['git', 'clone', repo_url, repo_path], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return jsonify({'error': 'Failed to clone repository', 'details': stderr.decode()}), 500

    # Return the path to the cloned repository
    return jsonify({'message': 'Repository cloned successfully', 'repo_path': repo_path}), 200

@app.route('/convert', methods=['POST'])
def convert_repo():
    repo_path = request.json.get('repo_path')
    if not repo_path or not os.path.exists(repo_path):
        return jsonify({'error': 'Invalid or missing repository path'}), 400
    
    try:
        json_file_path = convert_files_to_json(repo_path)
        return jsonify({'message': 'Files converted to JSON', 'json_path': json_file_path}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to convert files', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)