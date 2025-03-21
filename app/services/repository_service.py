import os
import shutil
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import ast  # For Python code analysis
import re
from collections import defaultdict

from flask import current_app
from app import mongo
from bson import ObjectId
import threading
import sys

class RepositoryService:
    @staticmethod
    def get_all_repositories(filters=None) -> List[Dict]:
        """
        Get all repositories from the database with optional filtering.
        
        Args:
            filters: Dictionary of filter criteria
        """
        query = {}
        
        if filters:
            # Status filter
            if 'status' in filters and filters['status'] not in ['all', 'All Status']:
                query['status'] = filters['status'].lower()
            
            # Language filter
            if 'language' in filters and filters['language'] not in ['all', 'All Languages']:
                query['languages.' + filters['language']] = {'$exists': True}
            
            # Size filter
            if 'size_min' in filters and 'size_max' in filters:
                try:
                    size_min = float(filters['size_min']) * 1024 * 1024  # Convert MB to bytes
                    size_max = float(filters['size_max']) * 1024 * 1024  # Convert MB to bytes
                    query['total_size'] = {'$gte': size_min, '$lte': size_max}
                except (ValueError, TypeError):
                    pass
            
            # Search filter
            if 'search' in filters and filters['search']:
                search_term = filters['search']
                query['$or'] = [
                    {'repo_url': {'$regex': search_term, '$options': 'i'}},
                    {'repo_name': {'$regex': search_term, '$options': 'i'}}
                ]
        
        repositories = list(mongo.db.repositories.find(query))
        
        # Convert ObjectId to string
        for repo in repositories:
            repo['_id'] = str(repo['_id'])
        
        return repositories

    @staticmethod
    def get_repository(repo_id: str) -> Optional[Dict]:
        """Get a repository by ID."""
        if not repo_id or repo_id == 'null' or repo_id == 'undefined' or repo_id == 'None':
            return None
            
        try:
            repo = mongo.db.repositories.find_one({'_id': ObjectId(repo_id)})
            if repo:
                repo['_id'] = str(repo['_id'])
            return repo
        except Exception as e:
            print(f"Error getting repository: {e}")
            return None

    @staticmethod
    def add_repository(repo_url: str) -> Dict:
        """Add a new repository to the database."""
        # Extract repo name from URL
        repo_name = repo_url.split('/')[-1]
        
        # Create a unique ID for the repository
        repo_id = ObjectId()
        
        # Create repository document
        repo = {
            '_id': repo_id,
            'repo_url': repo_url,
            'repo_name': repo_name,
            'repo_path': f"/tmp/repos/{repo_id}",
            'status': 'pending',
            'created_at': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'updated_at': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'file_count': 0,
            'directory_count': 0,
            'total_size': 0,
            'languages': {},
            'size_limit_mb': 500
        }
        
        # Insert into database
        mongo.db.repositories.insert_one(repo)
        
        # Convert ObjectId to string for JSON response
        repo['_id'] = str(repo['_id'])
        
        # Start background cloning process
        threading.Thread(target=RepositoryService._clone_and_analyze_repository, args=(repo,)).start()
        
        return repo

    @staticmethod
    def _clone_and_analyze_repository(repo: Dict):
        """Clone and analyze a repository in the background."""
        repo_id = repo['_id'] if isinstance(repo['_id'], ObjectId) else ObjectId(repo['_id'])
        repo_url = repo['repo_url']
        repo_path = repo['repo_path']
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(repo_path), exist_ok=True)
            
            # Clone repository
            subprocess.run(['git', 'clone', '--depth', '1', repo_url, repo_path], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Get repository stats
            stats = RepositoryService._get_repository_stats(repo_path)
            
            # Update repository status and stats
            mongo.db.repositories.update_one(
                {'_id': repo_id},
                {'$set': {
                    'status': 'completed',
                    'file_count': stats['file_count'],
                    'directory_count': stats['directory_count'],
                    'total_size': stats['total_size'],
                    'languages': stats['languages'],
                    'updated_at': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                }}
            )
        except Exception as e:
            # Update repository status to failed
            mongo.db.repositories.update_one(
                {'_id': repo_id},
                {'$set': {
                    'status': 'failed',
                    'error': str(e),
                    'updated_at': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                }}
            )

    @staticmethod
    def _get_repository_stats(repo_path: str) -> Dict:
        """Get statistics for a repository."""
        file_count = 0
        directory_count = 0
        total_size = 0
        languages = defaultdict(int)
        
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            directory_count += len(dirs)
            
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_count += 1
                
                # Get file extension for language stats
                _, ext = os.path.splitext(file)
                if ext:
                    languages[ext] = 1
        
        return {
            'file_count': file_count,
            'directory_count': directory_count,
            'total_size': total_size,
            'languages': dict(languages)
        }

    @staticmethod
    def delete_repository(repo_id: str) -> bool:
        """Delete a repository."""
        if not repo_id or repo_id == 'null' or repo_id == 'undefined':
                return False
            
        try:
            # Get repository
            repo = mongo.db.repositories.find_one({'_id': ObjectId(repo_id)})
            if not repo:
                return False
            
            # Delete repository directory
            repo_path = repo.get('repo_path')
            if repo_path and os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
            
            # Delete from database
            mongo.db.repositories.delete_one({'_id': ObjectId(repo_id)})
            
            return True
        except Exception as e:
            print(f"Error deleting repository: {e}")
            return False

    @staticmethod
    def analyze_repository_code(repo_id):
        """Analyze repository code structure and dependencies."""
        repo = RepositoryService.get_repository(repo_id)
        if not repo:
            return {'error': 'Repository not found'}
        
        # Check if repo is a dict (from error handling) or a Repository object
        if isinstance(repo, dict):
            if 'error' in repo:
                return repo
            repo_path = repo.get('repo_path')
        else:
            repo_path = repo.repo_path
        
        if not repo_path or not os.path.exists(repo_path):
            return {'error': 'Repository directory not found'}
        
        # Build file tree
        file_tree = {
            'name': os.path.basename(repo_path),
            'type': 'directory',
            'path': '/',
            'children': []
        }
        
        # Process all files and directories
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            # Get relative path from repo root
            rel_path = os.path.relpath(root, repo_path)
            if rel_path == '.':
                current_dir = file_tree
            else:
                # Create or get the current directory node
                current_dir = RepositoryService._get_or_create_dir_node(file_tree, rel_path)
            
            # Process directories
            for dir_name in dirs:
                dir_path = os.path.join(rel_path, dir_name)
                if dir_path == '.':
                    continue
                
                dir_node = {
                    'name': dir_name,
                    'type': 'directory',
                    'path': '/' + dir_path.replace('\\', '/'),
                    'children': []
                }
                current_dir['children'].append(dir_node)
            
            # Process files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_file_path = os.path.relpath(file_path, repo_path)
                abs_file_path = os.path.join(repo_path, rel_file_path)
                
                # Create file node
                file_node = {
                    'name': file_name,
                    'type': 'file',
                    'path': '/' + rel_file_path.replace('\\', '/'),
                    'extension': os.path.splitext(file_name)[1][1:] if os.path.splitext(file_name)[1] else '',
                    'size': os.path.getsize(abs_file_path)
                }
                
                # Extract functions and classes if it's a supported file type
                if file_name.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.java')):
                    functions, classes = RepositoryService._extract_functions_and_classes(abs_file_path, file_node['path'])
                    if functions:
                        file_node['functions'] = functions
                    if classes:
                        file_node['classes'] = classes
                
                # Extract imports
                imports = RepositoryService._extract_imports(abs_file_path, file_node['path'], repo_path)
                if imports:
                    file_node['imports'] = imports
                
                current_dir['children'].append(file_node)
        
        return file_tree

    @staticmethod
    def _get_or_create_dir_node(root, path):
        """Get or create a directory node in the tree."""
        if path == '.' or path == '':
            return root
        
        parts = path.split(os.sep)
        current = root
        
        for part in parts:
            found = False
            for child in current['children']:
                if child['name'] == part and child['type'] == 'directory':
                    current = child
                    found = True
                    break
            
            if not found:
                new_dir = {
                    'name': part,
                    'type': 'directory',
                    'path': '/' + os.path.join(*parts[:parts.index(part) + 1]).replace('\\', '/'),
                    'children': []
                }
                current['children'].append(new_dir)
                current = new_dir
        
        return current

    @staticmethod
    def _extract_functions_and_classes(file_path, file_rel_path):
        """Extract functions and classes from a file."""
        functions = []
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # JavaScript/TypeScript
            if file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                # Extract functions
                function_patterns = [
                    r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',  # function declarations
                    r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?function',  # function expressions
                    r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(',  # arrow functions
                ]
                
                for pattern in function_patterns:
                    for match in re.finditer(pattern, content):
                        func_name = match.group(1)
                        # Find function dependencies
                        func_content = RepositoryService._get_function_content(content, match.end())
                        dependencies = RepositoryService._extract_function_dependencies(func_content, file_rel_path)
                        
                        functions.append({
                            'name': func_name,
                            'type': 'function',
                            'dependencies': dependencies
                        })
                
                # Extract classes
                class_pattern = r'(?:export\s+)?class\s+(\w+)'
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    class_content = RepositoryService._get_class_content(content, match.end())
                    
                    # Extract methods
                    method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*{'
                    methods = []
                    
                    for method_match in re.finditer(method_pattern, class_content):
                        method_name = method_match.group(1)
                        if method_name not in ['constructor', 'get', 'set']:
                            method_content = RepositoryService._get_function_content(class_content, method_match.end())
                            dependencies = RepositoryService._extract_function_dependencies(method_content, file_rel_path)
                            
                            methods.append({
                                'name': method_name,
                                'type': 'method',
                                'dependencies': dependencies
                            })
                    
                    classes.append({
                        'name': class_name,
                        'type': 'class',
                        'methods': methods
                    })
            
            # Python
            elif file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        # Extract functions
                        if isinstance(node, ast.FunctionDef):
                            dependencies = []
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                                    dependencies.append({
                                        'target': child.func.id,
                                        'type': 'call',
                                        'line': child.lineno
                                    })
                            
                            functions.append({
                                'name': node.name,
                                'type': 'function',
                                'dependencies': dependencies
                            })
                        
                        # Extract classes
                        elif isinstance(node, ast.ClassDef):
                            methods = []
                            for child in node.body:
                                if isinstance(child, ast.FunctionDef):
                                    method_deps = []
                                    for method_child in ast.walk(child):
                                        if isinstance(method_child, ast.Call) and isinstance(method_child.func, ast.Name):
                                            method_deps.append({
                                                'target': method_child.func.id,
                                                'type': 'call',
                                                'line': method_child.lineno
                                            })
                                    
                                    methods.append({
                                        'name': child.name,
                                        'type': 'method',
                                        'dependencies': method_deps
                                    })
                            
                            classes.append({
                                'name': node.name,
                                'type': 'class',
                                'methods': methods
                            })
                except SyntaxError:
                    pass
            
            # Java
            elif file_path.endswith('.java'):
                # Extract classes
                class_pattern = r'(?:public|private|protected)?\s*class\s+(\w+)'
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    class_content = RepositoryService._get_class_content(content, match.end())
                    
                    # Extract methods
                    method_pattern = r'(?:public|private|protected)?\s+(?:static\s+)?[\w<>[\]]+\s+(\w+)\s*\([^)]*\)\s*{'
                    methods = []
                    
                    for method_match in re.finditer(method_pattern, class_content):
                        method_name = method_match.group(1)
                        method_content = RepositoryService._get_function_content(class_content, method_match.end())
                        dependencies = RepositoryService._extract_function_dependencies(method_content, file_rel_path)
                        
                        methods.append({
                            'name': method_name,
                            'type': 'method',
                            'dependencies': dependencies
                        })
                    
                    classes.append({
                        'name': class_name,
                        'type': 'class',
                        'methods': methods
                    })
        
        except Exception as e:
            print(f"Error extracting functions and classes from {file_path}: {e}")
        
        return functions, classes

    @staticmethod
    def _extract_imports(file_path, file_rel_path, repo_path):
        """Extract imports from a file."""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # JavaScript/TypeScript imports
            if file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                import_patterns = [
                    (r'import\s+{([^}]+)}\s+from\s+[\'"]([^\'"]+)[\'"]', True),  # Named imports
                    (r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', False),  # Default imports
                    (r'import\s+\*\s+as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', False),  # Namespace imports
                ]
                
                for pattern, is_named in import_patterns:
                    for match in re.finditer(pattern, content):
                        if is_named:
                            symbols = [s.strip() for s in match.group(1).split(',')]
                            module = match.group(2)
                        else:
                            symbols = [match.group(1)]
                            module = match.group(2)
                        
                        resolved_path = RepositoryService._resolve_js_dependency(module, file_path, repo_path)
                        if resolved_path:
                            imports.append({
                                'source': '/' + resolved_path.replace('\\', '/'),
                                'type': 'file',
                                'symbols': symbols
                            })
            
            # Python imports
            elif file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                imports.append({
                                    'source': name.name,
                                    'type': 'module',
                                    'symbols': [name.asname or name.name]
                                })
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ''
                            imports.append({
                                'source': module,
                                'type': 'module',
                                'symbols': [n.name for n in node.names]
                            })
                except SyntaxError:
                    pass
            
            # Java imports
            elif file_path.endswith('.java'):
                import_pattern = r'import\s+([^;]+);'
                for match in re.finditer(import_pattern, content):
                    import_path = match.group(1)
                    imports.append({
                        'source': import_path,
                        'type': 'package',
                        'symbols': [import_path.split('.')[-1]]
                    })
        
        except Exception as e:
            print(f"Error extracting imports from {file_path}: {e}")
        
        return imports

    @staticmethod
    def _get_function_content(content, start_pos):
        """Get the content of a function."""
        brace_count = 0
        in_string = False
        string_char = None
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if char in ['"', "'"]:
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    in_string = False
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return content[start_pos:i + 1]
        
        return content[start_pos:]

    @staticmethod
    def _get_class_content(content, start_pos):
        """Get the content of a class."""
        return RepositoryService._get_function_content(content, start_pos)

    @staticmethod
    def _extract_function_dependencies(content, file_path):
        """Extract function dependencies from function content."""
        dependencies = []
        
        # Extract function calls
        call_pattern = r'(\w+)\s*\('
        for match in re.finditer(call_pattern, content):
            func_name = match.group(1)
            # Skip common built-in functions and keywords
            if func_name not in ['if', 'for', 'while', 'switch', 'catch']:
                dependencies.append({
                    'target': f"{file_path}#{func_name}",
                    'type': 'call',
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return dependencies

    @staticmethod
    def get_repositories(page=1, limit=10, sort_by='created_at', sort_dir='desc'):
        """Get all repositories with pagination."""
        try:
            # Calculate skip value for pagination
            skip = (page - 1) * limit
            
            # Determine sort direction
            sort_direction = -1 if sort_dir.lower() == 'desc' else 1
            
            # Get repositories from database
            cursor = mongo.db.repositories.find().sort(sort_by, sort_direction).skip(skip).limit(limit)
            repositories = list(cursor)
            
            # Get total count for pagination
            total = mongo.db.repositories.count_documents({})
            
            return {
                'repositories': repositories,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit  # Ceiling division
                }
            }
        except Exception as e:
            print(f"Error getting repositories: {e}")
            return {'repositories': [], 'pagination': {'page': page, 'limit': limit, 'total': 0, 'pages': 0}} 

    @staticmethod
    def _register_exported_function(file_path, func_name):
        """Register an exported function for cross-file call detection."""
        if func_name not in RepositoryService._exported_functions:
            RepositoryService._exported_functions[func_name] = []
        RepositoryService._exported_functions[func_name].append(file_path)

    @staticmethod
    def _find_function_definition(func_name):
        """Find the file that defines a function."""
        if func_name in RepositoryService._exported_functions:
            # Return the first file that defines this function
            # In a more sophisticated implementation, we could use import analysis
            # to determine which specific file is being referenced
            return RepositoryService._exported_functions[func_name][0]
        return None

    @staticmethod
    def _resolve_python_dependency(module, file_path, base_path):
        """Resolve a Python import to a file path."""
        # Convert dot notation to directory structure
        module_path = module.replace('.', '/')
        
        # Check for .py file
        py_path = f"{module_path}.py"
        full_path = os.path.join(base_path, py_path)
        if os.path.exists(full_path):
            return py_path
        
        # Check for package (directory with __init__.py)
        init_path = f"{module_path}/__init__.py"
        full_init_path = os.path.join(base_path, init_path)
        if os.path.exists(full_init_path):
            return init_path
        
        return None

    @staticmethod
    def _resolve_java_dependency(module, file_path, base_path):
        """Resolve a Java import to a file path."""
        # Convert package notation to directory structure
        module_path = module.replace('.', '/')
        
        # Check for .java file
        java_path = f"{module_path}.java"
        full_path = os.path.join(base_path, java_path)
        if os.path.exists(full_path):
            return java_path
        
        return None

    @staticmethod
    def _get_language_from_extension(extension: str) -> str:
        """Get programming language from file extension."""
        extension = extension.lower().lstrip('.')
        language_map = {
            # Web languages
            'html': 'html',
            'htm': 'html',
            'css': 'css',
            'scss': 'scss',
            'sass': 'sass',
            'less': 'less',
            
            # JavaScript family
            'js': 'javascript',
            'jsx': 'jsx',
            'ts': 'typescript',
            'tsx': 'tsx',
            'json': 'json',
            
            # Backend languages
            'py': 'python',
            'rb': 'ruby',
            'php': 'php',
            'java': 'java',
            'c': 'c',
            'h': 'c',
            'cpp': 'cpp',
            'hpp': 'cpp',
            'cs': 'csharp',
            'go': 'go',
            'rs': 'rust',
            'swift': 'swift',
            'kt': 'kotlin',
            
            # Config and data files
            'yml': 'yaml',
            'yaml': 'yaml',
            'xml': 'xml',
            'toml': 'toml',
            'ini': 'ini',
            'cfg': 'ini',
            'conf': 'ini',
            
            # Shell scripts
            'sh': 'bash',
            'bash': 'bash',
            'zsh': 'bash',
            'bat': 'batch',
            'ps1': 'powershell',
            
            # Documentation
            'md': 'markdown',
            'markdown': 'markdown',
            'rst': 'restructuredtext',
            'txt': 'text',
            
            # Database
            'sql': 'sql',
        }
        
        return language_map.get(extension, 'text')

_exported_functions = {}  # Global registry of exported functions 