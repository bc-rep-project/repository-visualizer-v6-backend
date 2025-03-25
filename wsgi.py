import os
import sys
from dotenv import load_dotenv

# Ensure all required packages are available
try:
    import requests
except ImportError:
    print("ERROR: 'requests' package is missing. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Load environment variables
load_dotenv()

# Create the application instance
from app import create_app
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run() 