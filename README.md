# Repository Visualizer Backend

A Flask-based RESTful API service for managing GitHub repository cloning and analysis. This service provides endpoints for cloning repositories, tracking their status, and managing repository metadata.

## Tech Stack

- **Framework**: Flask 3.0.2
- **Database**: MongoDB
- **ORM**: SQLAlchemy
- **Rate Limiting**: Flask-Limiter with Redis support
- **CORS**: Flask-CORS
- **WSGI Server**: Gunicorn
- **Process Manager**: Gunicorn with workers

## Prerequisites

- Python 3.8+
- MongoDB 6.0+
- Git (for repository cloning)
- Redis (optional, for rate limiting)

## Local Development Setup

1. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/macOS
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=mongodb://localhost:27017/repo_visualizer
REDIS_URL=redis://localhost:6379/0  # Optional, for rate limiting
```

4. Ensure MongoDB is running:
```bash
# Check MongoDB status on Windows
sc query MongoDB

# Check MongoDB status on Unix/macOS
sudo systemctl status mongodb
```

5. Run the development server:
```bash
flask run
```

The API will be available at `http://localhost:5000`.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # App initialization and configuration
│   ├── config.py            # Configuration classes
│   ├── models/              # Database models
│   │   ├── __init__.py
│   │   └── repository.py
│   ├── routes/              # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── repository.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── repository_service.py
│   ├── utils/              # Helper functions
│   │   └── __init__.py
│   └── schemas/            # Request/Response schemas
│       └── __init__.py
├── migrations/             # Database migrations
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── wsgi.py               # WSGI entry point
└── .env                  # Environment variables
```

## API Endpoints

- `GET /` - Health check endpoint
- `GET /api/repositories` - List all repositories
- `POST /api/repositories` - Clone a new repository
- `GET /api/repositories/{repo_id}` - Get repository details
- `DELETE /api/repositories/{repo_id}` - Delete a repository

For detailed API documentation, see [API_DOCUMENTATION.md](../API_DOCUMENTATION.md).

## Configuration

The application uses a class-based configuration system:

- `Config`: Base configuration class
- `DevelopmentConfig`: Development environment settings
- `ProductionConfig`: Production environment settings
- `TestingConfig`: Testing environment settings

## Database Management

### Creating Migrations

```bash
flask db migrate -m "Description of changes"
```

### Applying Migrations

```bash
flask db upgrade
```

### Rolling Back Migrations

```bash
flask db downgrade
```

## Testing

Run tests using pytest:

```bash
python -m pytest
```

## Deployment (Render)

1. Connect your GitHub repository to Render

2. Create a new Web Service with these settings:
   - **Name**: repository-visualizer-backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Root Directory**: `./backend` (if using monorepo)

3. Add Environment Variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secure-secret-key
   DATABASE_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/repo_visualizer?retryWrites=true&w=majority
   REDIS_URL=redis://redis:6379/0  # Optional
   PYTHON_VERSION=3.11.0
   ```

4. Configure the Health Check:
   - **Path**: `/`
   - **Status**: 200
   - **Frequency**: 60s

5. Database Setup:
   - Create a MongoDB Atlas cluster
   - Create a database user with appropriate permissions
   - Add the MongoDB connection string to environment variables
   - Whitelist Render's IP addresses in MongoDB Atlas

### MongoDB Atlas Setup

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a database user:
   - Username and password
   - Read/Write permissions to the database
3. Get your connection string:
   - Click "Connect"
   - Choose "Connect your application"
   - Copy the connection string
4. Configure network access:
   - Add Render's IP addresses to the IP whitelist
   - Or allow access from anywhere (0.0.0.0/0)

### Troubleshooting Deployment

1. Application Errors:
   - Check Render logs for detailed error messages
   - Verify environment variables are set correctly
   - Ensure MongoDB connection string is properly formatted
   - Check MongoDB Atlas access logs

2. Build Errors:
   - Verify Python version in `runtime.txt`
   - Check requirements.txt for compatibility
   - Ensure Procfile is in the correct location
   - Verify gunicorn configuration

3. Database Errors:
   - Check MongoDB connection string format
   - Verify database user permissions
   - Check network access settings in MongoDB Atlas
   - Ensure MongoDB cluster is running

4. Common Solutions:
   - Clear build cache and redeploy
   - Check application logs for errors
   - Verify MongoDB Atlas connection
   - Test locally with production settings

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 200 requests per day per IP address
- 10 repository clone operations per minute per IP address

## CORS Configuration

CORS is configured to allow requests from:
- `https://repository-visualizer-v6-frontend.vercel.app`
- `http://localhost:3000` (development)

## Error Handling

The API uses consistent error responses:
```json
{
    "error": "Error message",
    "details": "Additional details (optional)"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Create a pull request

## Scripts

- `scripts/`: Contains utility scripts for database setup and maintenance

## Environment Variables

| Variable      | Description                | Required | Default                                    |
|--------------|----------------------------|----------|---------------------------------------------|
| FLASK_ENV    | Environment name           | No       | development                                |
| SECRET_KEY   | Flask secret key           | Yes      | -                                          |
| DATABASE_URL | MongoDB connection URL      | Yes      | mongodb://localhost:27017/repo_visualizer      |
| REDIS_URL    | Redis connection URL       | No       | memory://                                  |

## Troubleshooting

### Common Issues

1. Database connection errors:
   - Check MongoDB service is running
   - Verify DATABASE_URL in .env
   - Ensure database exists

2. Git errors:
   - Verify Git is installed
   - Check repository URL format
   - Ensure sufficient disk space

3. Rate limiting issues:
   - Check Redis connection (if configured)
   - Verify rate limit configuration

## License

MIT License 