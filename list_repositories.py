from app import create_app, mongo
app = create_app()

with app.app_context():
    print('Available repositories:')
    for repo in mongo.repositories.find():
        print(f"ID: {repo.get('_id')}, Name: {repo.get('repo_name', 'Unnamed')}, Path: {repo.get('repo_path')}")