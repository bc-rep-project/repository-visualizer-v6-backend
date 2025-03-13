# Repository Visualizer API Documentation

This document provides detailed information about the Repository Visualizer API endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:5000/api
```

For production:

```
https://repository-visualizer-backend.onrender.com/api
```

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## API Endpoints

### Repository Management

#### List Repositories

Retrieves a list of all repositories.

- **URL**: `/repositories`
- **Method**: `GET`
- **Response Format**: JSON

**Response Example**:

```json
{
  "repositories": [
    {
      "id": "64a7b3e12f8f9a1c2d3e4f5a",
      "name": "example-repo",
      "url": "https://github.com/username/example-repo.git",
      "status": "cloned",
      "created_at": "2023-07-07T12:34:56.789Z",
      "updated_at": "2023-07-07T12:45:12.345Z",
      "description": "An example repository",
      "size": 1024,
      "language": "JavaScript",
      "stars": 42,
      "forks": 10
    },
    {
      "id": "64a7b3e12f8f9a1c2d3e4f5b",
      "name": "another-repo",
      "url": "https://github.com/username/another-repo.git",
      "status": "cloning",
      "created_at": "2023-07-08T10:11:12.131Z",
      "updated_at": "2023-07-08T10:11:12.131Z",
      "description": "Another example repository",
      "size": 2048,
      "language": "Python",
      "stars": 21,
      "forks": 5
    }
  ]
}
```

#### Get Repository

Retrieves details for a specific repository.

- **URL**: `/repositories/:id`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Response Format**: JSON

**Response Example**:

```json
{
  "repository": {
    "id": "64a7b3e12f8f9a1c2d3e4f5a",
    "name": "example-repo",
    "url": "https://github.com/username/example-repo.git",
    "status": "cloned",
    "created_at": "2023-07-07T12:34:56.789Z",
    "updated_at": "2023-07-07T12:45:12.345Z",
    "description": "An example repository",
    "size": 1024,
    "language": "JavaScript",
    "stars": 42,
    "forks": 10,
    "file_count": 120,
    "directory_count": 25,
    "languages": {
      "JavaScript": 75,
      "HTML": 15,
      "CSS": 10
    }
  }
}
```

#### Clone Repository

Initiates the cloning of a repository.

- **URL**: `/repositories/clone`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Request Body**:

```json
{
  "url": "https://github.com/username/repo-name.git"
}
```

**Response Example**:

```json
{
  "repository": {
    "id": "64a7b3e12f8f9a1c2d3e4f5c",
    "name": "repo-name",
    "url": "https://github.com/username/repo-name.git",
    "status": "cloning",
    "created_at": "2023-07-09T15:16:17.181Z",
    "updated_at": "2023-07-09T15:16:17.181Z"
  },
  "message": "Repository cloning started"
}
```

#### Delete Repository

Deletes a repository.

- **URL**: `/repositories/:id`
- **Method**: `DELETE`
- **URL Parameters**: `id` - Repository ID
- **Response Format**: JSON

**Response Example**:

```json
{
  "message": "Repository deleted successfully",
  "id": "64a7b3e12f8f9a1c2d3e4f5a"
}
```

### Repository Analysis

#### Analyze Repository

Initiates or retrieves the analysis of a repository's code structure.

- **URL**: `/repositories/:id/analyze`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Response Format**: JSON

**Response Example**:

```json
{
  "analysis": {
    "repository_id": "64a7b3e12f8f9a1c2d3e4f5a",
    "status": "completed",
    "created_at": "2023-07-07T13:00:00.000Z",
    "updated_at": "2023-07-07T13:05:23.456Z",
    "file_count": 120,
    "directory_count": 25,
    "function_count": 350,
    "class_count": 42,
    "languages": {
      "JavaScript": 75,
      "HTML": 15,
      "CSS": 10
    },
    "tree_structure": {
      "name": "example-repo",
      "type": "directory",
      "path": "/",
      "size": 1024,
      "children": [
        {
          "name": "src",
          "type": "directory",
          "path": "/src",
          "size": 768,
          "children": [
            {
              "name": "index.js",
              "type": "file",
              "path": "/src/index.js",
              "size": 2.5,
              "language": "JavaScript",
              "functions": [
                {
                  "name": "main",
                  "start_line": 10,
                  "end_line": 20,
                  "calls": ["renderApp", "initializeStore"]
                }
              ]
            }
          ]
        }
      ]
    },
    "dependencies": [
      {
        "source": "/src/index.js",
        "target": "/src/components/App.js",
        "type": "import"
      },
      {
        "source": "/src/components/App.js:renderApp",
        "target": "/src/utils/helpers.js:formatData",
        "type": "function_call"
      }
    ]
  }
}
```

#### Get Repository File Structure

Retrieves the file structure of a repository.

- **URL**: `/repositories/:id/structure`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Response Format**: JSON

**Response Example**:

```json
{
  "structure": {
    "name": "example-repo",
    "type": "directory",
    "path": "/",
    "size": 1024,
    "children": [
      {
        "name": "src",
        "type": "directory",
        "path": "/src",
        "size": 768,
        "children": [
          {
            "name": "index.js",
            "type": "file",
            "path": "/src/index.js",
            "size": 2.5,
            "language": "JavaScript"
          },
          {
            "name": "components",
            "type": "directory",
            "path": "/src/components",
            "size": 512,
            "children": [
              {
                "name": "App.js",
                "type": "file",
                "path": "/src/components/App.js",
                "size": 3.2,
                "language": "JavaScript"
              }
            ]
          }
        ]
      },
      {
        "name": "package.json",
        "type": "file",
        "path": "/package.json",
        "size": 1.8,
        "language": "JSON"
      }
    ]
  }
}
```

#### Get Repository Dependencies

Retrieves the dependencies between files in a repository.

- **URL**: `/repositories/:id/dependencies`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Response Format**: JSON

**Response Example**:

```json
{
  "dependencies": [
    {
      "source": "/src/index.js",
      "target": "/src/components/App.js",
      "type": "import"
    },
    {
      "source": "/src/components/App.js",
      "target": "/src/utils/helpers.js",
      "type": "import"
    },
    {
      "source": "/src/components/App.js:renderApp",
      "target": "/src/utils/helpers.js:formatData",
      "type": "function_call"
    }
  ]
}
```

#### Get Repository Functions

Retrieves the functions defined in a repository.

- **URL**: `/repositories/:id/functions`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Query Parameters**:
  - `file` (optional) - Filter functions by file path
  - `language` (optional) - Filter functions by language
- **Response Format**: JSON

**Response Example**:

```json
{
  "functions": [
    {
      "name": "renderApp",
      "file_path": "/src/components/App.js",
      "start_line": 15,
      "end_line": 30,
      "language": "JavaScript",
      "calls": ["formatData", "createElement"]
    },
    {
      "name": "formatData",
      "file_path": "/src/utils/helpers.js",
      "start_line": 5,
      "end_line": 12,
      "language": "JavaScript",
      "calls": []
    }
  ]
}
```

### Repository Statistics

#### Get Repository Language Statistics

Retrieves statistics about languages used in a repository.

- **URL**: `/repositories/:id/languages`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Response Format**: JSON

**Response Example**:

```json
{
  "languages": {
    "JavaScript": 75,
    "HTML": 15,
    "CSS": 10,
    "JSON": 5
  },
  "total_bytes": 1024000
}
```

#### Get Repository Commit History

Retrieves the commit history of a repository.

- **URL**: `/repositories/:id/commits`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Query Parameters**:
  - `limit` (optional) - Number of commits to return (default: 50)
  - `offset` (optional) - Offset for pagination (default: 0)
- **Response Format**: JSON

**Response Example**:

```json
{
  "commits": [
    {
      "hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
      "author": "John Doe",
      "email": "john.doe@example.com",
      "date": "2023-07-06T12:34:56.789Z",
      "message": "Fix bug in login component",
      "files_changed": 3,
      "insertions": 25,
      "deletions": 10
    },
    {
      "hash": "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1",
      "author": "Jane Smith",
      "email": "jane.smith@example.com",
      "date": "2023-07-05T10:11:12.131Z",
      "message": "Add new feature",
      "files_changed": 5,
      "insertions": 120,
      "deletions": 15
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

### File Operations

#### Get File Content

Retrieves the content of a specific file in a repository.

- **URL**: `/repositories/:id/files`
- **Method**: `GET`
- **URL Parameters**: `id` - Repository ID
- **Query Parameters**:
  - `path` (required) - Path to the file relative to the repository root
- **Response Format**: JSON

**Response Example**:

```json
{
  "file": {
    "name": "index.js",
    "path": "/src/index.js",
    "size": 2560,
    "language": "JavaScript",
    "content": "import React from 'react';\nimport ReactDOM from 'react-dom';\nimport App from './components/App';\n\nReactDOM.render(<App />, document.getElementById('root'));\n"
  }
}
```

## Error Responses

The API returns standard HTTP status codes to indicate the success or failure of a request.

### Common Error Codes

- `400 Bad Request` - The request was malformed or missing required parameters
- `404 Not Found` - The requested resource was not found
- `500 Internal Server Error` - An unexpected error occurred on the server

### Error Response Format

```json
{
  "error": {
    "code": 404,
    "message": "Repository not found",
    "details": "No repository found with ID 64a7b3e12f8f9a1c2d3e4f5z"
  }
}
```

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

## Versioning

The API is currently at version 1. The version is not included in the URL path but may be in future releases.

## Data Models

### Repository Object

| Field | Type | Description |
|-------|------|-------------|
| id | String | Unique identifier for the repository |
| name | String | Name of the repository |
| url | String | Git URL of the repository |
| status | String | Status of the repository (cloning, cloned, error) |
| created_at | Date | When the repository was added to the system |
| updated_at | Date | When the repository was last updated |
| description | String | Description of the repository |
| size | Number | Size of the repository in KB |
| language | String | Primary language of the repository |
| stars | Number | Number of stars on GitHub |
| forks | Number | Number of forks on GitHub |

### Analysis Object

| Field | Type | Description |
|-------|------|-------------|
| repository_id | String | ID of the repository |
| status | String | Status of the analysis (pending, in_progress, completed, error) |
| created_at | Date | When the analysis was started |
| updated_at | Date | When the analysis was last updated |
| file_count | Number | Number of files in the repository |
| directory_count | Number | Number of directories in the repository |
| function_count | Number | Number of functions detected |
| class_count | Number | Number of classes detected |
| languages | Object | Percentage breakdown of languages |
| tree_structure | Object | Hierarchical structure of the repository |
| dependencies | Array | List of dependencies between files |

## Webhook Support

The API currently does not support webhooks. This feature may be added in future versions.

## Examples

### Cloning and Analyzing a Repository

1. Clone a repository:

```bash
curl -X POST http://localhost:5000/api/repositories/clone \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/username/repo-name.git"}'
```

2. Check repository status:

```bash
curl -X GET http://localhost:5000/api/repositories/{repository_id}
```

3. Analyze the repository:

```bash
curl -X GET http://localhost:5000/api/repositories/{repository_id}/analyze
```

4. Retrieve the analysis results:

```bash
curl -X GET http://localhost:5000/api/repositories/{repository_id}/analyze
```

## Changelog

### v1.0.0 (2023-07-01)

- Initial release of the API
- Support for repository cloning and basic analysis
- File structure and dependency visualization

### v1.1.0 (2023-08-15)

- Added support for function-level analysis
- Improved language detection
- Added commit history endpoint

## Support

For API support, please contact the development team at support@repository-visualizer.com or open an issue on the GitHub repository. 