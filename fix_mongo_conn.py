import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment
mongo_uri = os.environ.get('MONGO_URI') or os.environ.get('DATABASE_URL')
if not mongo_uri:
    print("Error: No MongoDB connection string found in environment variables")
    exit(1)

print(f"Connecting to MongoDB with URI: {mongo_uri}")

try:
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    
    # List all databases
    print("\nAvailable databases:")
    for db_name in client.list_database_names():
        print(f"- {db_name}")
    
    # Choose the right database
    # The URI shows Cluster0 but we need to confirm what's actually used
    # First, try "repo_visualizer" which is what the code expects
    db_name = "repo_visualizer"
    db = client[db_name]
    
    # Check collections
    print(f"\nCollections in {db_name} database:")
    collections = db.list_collection_names()
    if collections:
        for collection in collections:
            print(f"- {collection}")
    else:
        print("No collections found. This may be the wrong database.")
        
        # Try Cluster0 as an alternative
        db_name = "Cluster0"
        db = client[db_name]
        print(f"\nCollections in {db_name} database:")
        collections = db.list_collection_names()
        for collection in collections:
            print(f"- {collection}")
    
    # If we've found the database with repository data, let's create necessary collections
    if "repositories" in db.list_collection_names():
        print("\nFound repository data. Creating/updating auto-save collections...")
        
        # Make sure the settings collection exists with auto-save settings
        result = db.settings.update_one(
            {},
            {"$set": {
                "autoSave": {
                    "repositories": True,
                    "analysis": True,
                    "enhancedAnalysis": True,
                    "interval": 15
                }
            }},
            upsert=True
        )
        print(f"Updated settings: {result.matched_count} matched, {result.modified_count} modified, {result.upserted_id and 'inserted' or 'not inserted'}")
        
        # Create repository_analyses and enhanced_repository_analyses collections if they don't exist
        if "repository_analyses" not in db.list_collection_names():
            # Take a repository ID to use for sample data
            repo = db.repositories.find_one()
            if repo:
                repo_id = str(repo["_id"])
                db.repository_analyses.insert_one({
                    "repository_id": repo_id,
                    "analysis": {"sample": True},
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                    "last_manual_save": datetime.utcnow().isoformat() + "Z"
                })
                print(f"Created repository_analyses collection with sample data for repo {repo_id}")
        
        if "enhanced_repository_analyses" not in db.list_collection_names():
            # Take a repository ID to use for sample data
            repo = db.repositories.find_one()
            if repo:
                repo_id = str(repo["_id"])
                db.enhanced_repository_analyses.insert_one({
                    "repository_id": repo_id,
                    "enhanced_analysis": {"sample": True},
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                    "last_manual_save": datetime.utcnow().isoformat() + "Z"
                })
                print(f"Created enhanced_repository_analyses collection with sample data for repo {repo_id}")
                
        # Create auto_save_stats collection if it doesn't exist
        if "auto_save_stats" not in db.list_collection_names():
            db.auto_save_stats.insert_one({
                "last_run": datetime.utcnow().isoformat() + "Z",
                "repositories_saved": 0,
                "analyses_saved": 0,
                "enhanced_analyses_saved": 0
            })
            print("Created auto_save_stats collection with initial data")
        
        # List all collections again to verify our changes
        print("\nCollections after updates:")
        for collection in db.list_collection_names():
            count = db[collection].count_documents({})
            print(f"- {collection}: {count} documents")
    
    else:
        print("\nCouldn't find repositories collection. Make sure you're connecting to the correct database.")
    
except Exception as e:
    print(f"Error: {e}") 