#!/usr/bin/env python3
import os
from pymongo import MongoClient
import re

# Read MongoDB URI from .env file
mongo_uri = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('MONGO_URI='):
            mongo_uri = line.split('=', 1)[1].strip()
            break

if not mongo_uri:
    print("MongoDB URI not found in .env file")
    exit(1)

print(f"Connecting to MongoDB with URI: {mongo_uri}")

try:
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client.get_database()
    
    # Check connection
    print(f"MongoDB connection successful")
    print(f"Database name: {db.name}")
    
    # List collections
    print("Collections:", db.list_collection_names())
    
    # Get repositories count
    repo_count = db.repositories.count_documents({})
    print(f"Total repositories: {repo_count}")
    
    # Print sample repositories
    print("\nSample repositories:")
    for repo in db.repositories.find().limit(3):
        repo_id = str(repo.get('_id'))
        repo_name = repo.get('repo_name', 'Unknown')
        print(f"ID: {repo_id}, Name: {repo_name}")
        
        # Check languages
        languages = repo.get('languages', {})
        print(f"Languages: {languages}")
        
        # Check for Python language
        if '.py' in languages:
            print(f"Repository has Python (.py) language!")
    
    # Instead of using direct MongoDB query syntax for dotted keys, 
    # we'll loop through all repositories and filter them in Python
    print("\nManual filtering for Python language:")
    python_repos = []
    for repo in db.repositories.find():
        languages = repo.get('languages', {})
        if '.py' in languages:
            python_repos.append(repo)
            print(f"Found Python repo - ID: {str(repo.get('_id'))}, Name: {repo.get('repo_name', 'Unknown')}")
            print(f"Languages: {languages}")
    
    print(f"\nTotal Python repositories (manual filter): {len(python_repos)}")
    
    # Try a different approach with $regex
    print("\nTrying $regex approach:")
    # Use a regex to match any field in the languages object that ends with 'py'
    regex_query = {'$or': [
        # Try to match .py at the end of any key in languages
        {'languages': {'$exists': True}}
    ]}
    
    for repo in db.repositories.find(regex_query).limit(10):
        languages = repo.get('languages', {})
        if any(k.endswith('.py') for k in languages.keys()):
            print(f"Found repo with Python using regex - ID: {str(repo.get('_id'))}")
            print(f"Languages: {languages}")
    
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    import traceback
    traceback.print_exc() 