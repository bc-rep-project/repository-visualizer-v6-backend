import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variables
mongo_uri = os.environ.get('MONGO_URI')
if not mongo_uri:
    print("Error: MONGO_URI not found in environment variables")
    exit(1)

try:
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client.get_database()
    
    # Print collections
    print("\nCollections in database:")
    collections = db.list_collection_names()
    for collection in collections:
        print(f"- {collection}")
    
    # Count documents in important collections
    print("\nDocument counts:")
    try:
        print(f"- repositories: {db.repositories.count_documents({})}")
    except Exception as e:
        print(f"- repositories: Error counting documents: {e}")
    
    try:
        print(f"- repository_analyses: {db.repository_analyses.count_documents({})}")
    except Exception as e:
        print(f"- repository_analyses: Error counting documents: {e}")
    
    try:
        print(f"- enhanced_repository_analyses: {db.enhanced_repository_analyses.count_documents({})}")
    except Exception as e:
        print(f"- enhanced_repository_analyses: Error counting documents: {e}")
    
    try:
        print(f"- auto_save_stats: {db.auto_save_stats.count_documents({})}")
    except Exception as e:
        print(f"- auto_save_stats: Error counting documents: {e}")
    
    try:
        print(f"- settings: {db.settings.count_documents({})}")
    except Exception as e:
        print(f"- settings: Error counting documents: {e}")
    
    # Show latest documents from important collections
    print("\nLatest repository analysis:")
    latest_analysis = db.repository_analyses.find_one(
        sort=[("updated_at", -1)]
    )
    if latest_analysis:
        print(f"- ID: {latest_analysis.get('repository_id')}")
        print(f"- Updated at: {latest_analysis.get('updated_at')}")
        if 'last_manual_save' in latest_analysis:
            print(f"- Last manual save: {latest_analysis.get('last_manual_save')}")
        if 'last_auto_save' in latest_analysis:
            print(f"- Last auto save: {latest_analysis.get('last_auto_save')}")
    else:
        print("No repository analyses found")
    
    print("\nLatest enhanced repository analysis:")
    latest_enhanced = db.enhanced_repository_analyses.find_one(
        sort=[("updated_at", -1)]
    )
    if latest_enhanced:
        print(f"- ID: {latest_enhanced.get('repository_id')}")
        print(f"- Updated at: {latest_enhanced.get('updated_at')}")
        if 'last_manual_save' in latest_enhanced:
            print(f"- Last manual save: {latest_enhanced.get('last_manual_save')}")
        if 'last_auto_save' in latest_enhanced:
            print(f"- Last auto save: {latest_enhanced.get('last_auto_save')}")
    else:
        print("No enhanced repository analyses found")
    
except Exception as e:
    print(f"Error connecting to MongoDB: {e}") 