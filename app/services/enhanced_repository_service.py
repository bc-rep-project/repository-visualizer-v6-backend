import os
import re
import ast
from typing import Dict, List, Tuple, Optional
from app.services.repository_service import RepositoryService

class EnhancedRepositoryService:
    @staticmethod
    def analyze_repository_code(repo_id: str) -> Dict:
        """Analyze repository code structure and dependencies with enhanced output."""
        repo = RepositoryService.get_repository(repo_id)
        if not repo:
            return {'error': 'Repository not found'}
        
        repo_path = repo.get('repo_path') if isinstance(repo, dict) else repo.repo_path
        if not repo_path or not os.path.exists(repo_path):
            return {'error': 'Repository directory not found'}
        
        # Build file tree
        file_tree = {
            'name': 'root',
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
            current_dir = file_tree if rel_path == '.' else EnhancedRepositoryService._get_or_create_dir_node(file_tree, rel_path)
            
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
                    functions, classes = EnhancedRepositoryService._extract_functions_and_classes(abs_file_path, file_node['path'])
                    if functions:
                        file_node['functions'] = functions
                    if classes:
                        file_node['classes'] = classes
                
                # Extract imports
                imports = EnhancedRepositoryService._extract_imports(abs_file_path, file_node['path'], repo_path)
                if imports:
                    file_node['imports'] = imports
                
                current_dir['children'].append(file_node)
        
        return file_tree

    @staticmethod
    def _get_or_create_dir_node(root: Dict, path: str) -> Dict:
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
    def _extract_functions_and_classes(file_path: str, file_rel_path: str) -> Tuple[List[Dict], List[Dict]]:
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
                        func_content = EnhancedRepositoryService._get_function_content(content, match.end())
                        dependencies = EnhancedRepositoryService._extract_function_dependencies(func_content, file_rel_path)
                        
                        functions.append({
                            'name': func_name,
                            'type': 'function',
                            'dependencies': dependencies
                        })
                
                # Extract classes
                class_pattern = r'(?:export\s+)?class\s+(\w+)'
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    class_content = EnhancedRepositoryService._get_class_content(content, match.end())
                    
                    # Extract methods
                    method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*{'
                    methods = []
                    
                    for method_match in re.finditer(method_pattern, class_content):
                        method_name = method_match.group(1)
                        if method_name not in ['constructor', 'get', 'set']:
                            method_content = EnhancedRepositoryService._get_function_content(class_content, method_match.end())
                            dependencies = EnhancedRepositoryService._extract_function_dependencies(method_content, file_rel_path)
                            
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
                    class_content = EnhancedRepositoryService._get_class_content(content, match.end())
                    
                    # Extract methods
                    method_pattern = r'(?:public|private|protected)?\s+(?:static\s+)?[\w<>[\]]+\s+(\w+)\s*\([^)]*\)\s*{'
                    methods = []
                    
                    for method_match in re.finditer(method_pattern, class_content):
                        method_name = method_match.group(1)
                        method_content = EnhancedRepositoryService._get_function_content(class_content, method_match.end())
                        dependencies = EnhancedRepositoryService._extract_function_dependencies(method_content, file_rel_path)
                        
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
    def _extract_imports(file_path: str, file_rel_path: str, repo_path: str) -> List[Dict]:
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
    def _get_function_content(content: str, start_pos: int) -> str:
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
    def _get_class_content(content: str, start_pos: int) -> str:
        """Get the content of a class."""
        return EnhancedRepositoryService._get_function_content(content, start_pos)

    @staticmethod
    def _extract_function_dependencies(content: str, file_path: str) -> List[Dict]:
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