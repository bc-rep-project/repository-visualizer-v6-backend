# Repository Visualizer Backend

A Flask-based RESTful API service for managing GitHub repository cloning and analysis. This service provides endpoints for cloning repositories, tracking their status, and managing repository metadata.

## Tech Stack

- **Framework**: Flask 3.0.2
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Rate Limiting**: Flask-Limiter with Redis support
- **CORS**: Flask-CORS
- **WSGI Server**: Gunicorn
- **Process Manager**: Gunicorn with workers

## Prerequisites

- Python 3.8+
- PostgreSQL 13+
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
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/repo_visualizer
REDIS_URL=redis://localhost:6379/0  # Optional, for rate limiting
```

4. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
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
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/repo_visualizer
   REDIS_URL=redis://redis:6379/0  # Optional
   PYTHON_VERSION=3.11.0
   ```

4. Configure the Health Check:
   - **Path**: `/`
   - **Status**: 200
   - **Frequency**: 60s

5. Database Setup:
   - Create a PostgreSQL database in Render
   - Add the provided DATABASE_URL to environment variables
   - Run migrations after first deploy:
     ```bash
     render run python -m flask db upgrade
     ```

### Troubleshooting Deployment

1. Application Errors:
   - Check Render logs for detailed error messages
   - Verify environment variables are set correctly
   - Ensure DATABASE_URL is properly configured
   - Check if migrations are applied

2. Build Errors:
   - Verify Python version in `runtime.txt`
   - Check requirements.txt for compatibility
   - Ensure Procfile is in the correct location
   - Verify gunicorn configuration

3. Database Errors:
   - Check DATABASE_URL format
   - Verify database exists and is accessible
   - Ensure migrations are up to date
   - Check database connection limits

4. Common Solutions:
   - Clear build cache and redeploy
   - Check application logs for errors
   - Verify file structure matches deployment config
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
| DATABASE_URL | PostgreSQL connection URL  | Yes      | postgresql://postgres:postgres@localhost:5432/repo_visualizer |
| REDIS_URL    | Redis connection URL       | No       | memory://                                  |

## Troubleshooting

### Common Issues

1. Database connection errors:
   - Check PostgreSQL service is running
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