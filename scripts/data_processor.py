import os
import json

def convert_to_txt(repo_path):
    """Converts specific file extensions to .txt within the repository."""
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.js', '.ts', '.py', '.tsx', '.jsx')):
                base = os.path.splitext(file)[0]
                os.rename(os.path.join(root, file), os.path.join(root, base + ".txt"))

def convert_files_to_json(repo_path):
    """Converts .txt files in the repository to a single .json file."""
    convert_to_txt(repo_path)
    data = {}
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    try:
                        # Attempt to load as JSON (in case it's a .js file with JSON content)
                        content = json.load(f)
                    except json.JSONDecodeError:
                        # Otherwise, read as plain text
                        f.seek(0)  # Reset file pointer after attempting to read as JSON
                        content = f.read()
                
                # Construct a relative path from repo_path to the file
                rel_path = os.path.relpath(file_path, repo_path)
                data[rel_path] = content

    json_file_path = os.path.join(repo_path, 'data.json')
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    return json_file_path