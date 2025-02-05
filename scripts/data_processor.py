import os
import json
import shutil
from pathlib import Path

def get_file_content(file_path):
    """Read and return the content of a file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def convert_files_to_json(repo_path):
    """
    Convert files with specific extensions to .txt and then to JSON format.
    Returns the path to the generated JSON file.
    """
    target_extensions = {'.js', '.ts', '.py', '.tsx', '.jsx'}
    file_data = []
    
    # Walk through the repository
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = Path(os.path.join(root, file))
            if file_path.suffix in target_extensions:
                try:
                    # Create relative path for structure preservation
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    # Read original file content
                    content = get_file_content(file_path)
                    
                    # Create txt file path
                    txt_path = file_path.with_suffix('.txt')
                    
                    # Copy content to txt file
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Store file information
                    file_data.append({
                        'original_path': relative_path,
                        'original_extension': file_path.suffix,
                        'content': content,
                        'lines': len(content.splitlines()),
                        'size': os.path.getsize(file_path)
                    })
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    # Create JSON output
    output = {
        'repository_stats': {
            'total_files': len(file_data),
            'extensions': list(set(item['original_extension'] for item in file_data))
        },
        'files': file_data
    }
    
    # Save JSON file
    json_output_path = os.path.join(repo_path, 'file_analysis.json')
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    return json_output_path