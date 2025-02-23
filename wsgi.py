import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create the application instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run() 