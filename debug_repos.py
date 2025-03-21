from app import create_app, mongo
import json

app = create_app()

with app.app_context():
    print("Checking repositories in the database...")
    
    # Print the total count of repositories
    total = mongo.db.repositories.count_documents({})
    print(f"Total repositories: {total}")
    
    # Print the first few repositories with their language data
    for repo in mongo.db.repositories.find().limit(5):
        repo_id = str(repo.get('_id'))
        repo_name = repo.get('repo_name')
        languages = repo.get('languages', {})
        
        print(f"\nRepository: {repo_name} (ID: {repo_id})")
        print(f"Languages: {json.dumps(languages, indent=2)}")
        
        # Try a direct query for Python files
        py_query = {"_id": repo.get('_id'), "languages..py": {"$exists": True}}
        has_py = mongo.db.repositories.count_documents(py_query)
        print(f"Query 'languages..py': {has_py} matches")
        
        # Try without the extra dot
        py_query2 = {"_id": repo.get('_id'), "languages.py": {"$exists": True}}
        has_py2 = mongo.db.repositories.count_documents(py_query2)
        print(f"Query 'languages.py': {has_py2} matches")
        
        # Check if .py exists directly in languages dict
        print(f"Direct check 'languages' dict: '.py' in keys: {'.py' in languages}")
        print(f"Direct check 'languages' dict: 'py' in keys: {'py' in languages}")