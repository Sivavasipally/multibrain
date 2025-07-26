# RAG Chatbot PWA API Documentation

This document provides comprehensive documentation for the RAG Chatbot PWA REST API.

## Base URL

- **Development**: `http://localhost:5000/api`
- **Production**: `https://your-domain.com/api`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Interactive Documentation

- **Swagger UI**: `/api/docs` - Interactive API explorer
- **ReDoc**: `/api/docs/redoc` - Clean, responsive documentation
- **OpenAPI Spec**: `/api/docs/openapi.json` - Machine-readable specification

## Endpoints Overview

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user
- `GET /auth/profile` - Get user profile
- `POST /auth/logout` - Logout user

### Context Management
- `GET /contexts` - List all contexts
- `POST /contexts` - Create a new context
- `GET /contexts/{id}` - Get context details
- `PUT /contexts/{id}` - Update context
- `DELETE /contexts/{id}` - Delete context
- `POST /contexts/{id}/reprocess` - Reprocess context

### Chat Management
- `GET /chat/sessions` - List chat sessions
- `POST /chat/sessions` - Create chat session
- `GET /chat/sessions/{id}` - Get session with messages
- `DELETE /chat/sessions/{id}` - Delete session
- `POST /chat/query` - Send chat message

### File Upload
- `POST /upload/files` - Upload files
- `GET /upload/supported-extensions` - Get supported file types

## Detailed Endpoint Documentation

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2023-01-01T00:00:00Z",
    "is_active": true
  }
}
```

#### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2023-01-01T00:00:00Z",
    "is_active": true
  }
}
```

### Context Management Endpoints

#### Create Context
```http
POST /contexts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Project Documentation",
  "description": "Documentation for my software project",
  "source_type": "files",
  "chunk_strategy": "language-specific",
  "embedding_model": "text-embedding-004",
  "config": {
    "file_paths": ["README.md", "docs/"],
    "include_extensions": [".md", ".txt", ".py"],
    "exclude_patterns": ["*.log", "node_modules/"]
  }
}
```

**Response (201 Created):**
```json
{
  "context": {
    "id": 1,
    "name": "My Project Documentation",
    "description": "Documentation for my software project",
    "source_type": "files",
    "status": "pending",
    "progress": 0,
    "total_chunks": 0,
    "total_tokens": 0,
    "config": {
      "file_paths": ["README.md", "docs/"],
      "include_extensions": [".md", ".txt", ".py"],
      "exclude_patterns": ["*.log", "node_modules/"]
    },
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

#### Get Context Details
```http
GET /contexts/1
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "context": {
    "id": 1,
    "name": "My Project Documentation",
    "description": "Documentation for my software project",
    "source_type": "files",
    "status": "ready",
    "progress": 100,
    "total_chunks": 150,
    "total_tokens": 50000,
    "config": {
      "file_paths": ["README.md", "docs/"]
    },
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T01:00:00Z",
    "documents": [
      {
        "id": 1,
        "filename": "README.md",
        "file_type": "markdown",
        "file_size": 2048,
        "chunks_count": 5,
        "tokens_count": 500,
        "language": "markdown",
        "processed_at": "2023-01-01T00:30:00Z"
      }
    ]
  }
}
```

### Chat Endpoints

#### Send Chat Message
```http
POST /chat/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": 1,
  "message": "What is the main purpose of this project?",
  "context_ids": [1, 2],
  "stream": false
}
```

**Response (200 OK):**
```json
{
  "message": {
    "id": 2,
    "role": "assistant",
    "content": "Based on the documentation, this project is a RAG (Retrieval-Augmented Generation) chatbot PWA that allows users to create contexts from various sources and chat with their data using AI.",
    "context_ids": [1, 2],
    "citations": [
      {
        "context_name": "My Project Documentation",
        "source": "README.md",
        "score": 0.95
      }
    ],
    "created_at": "2023-01-01T00:00:01Z"
  },
  "citations": [
    {
      "context_name": "My Project Documentation",
      "source": "README.md",
      "score": 0.95
    }
  ]
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Missing required field: username"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied"
}
```

### 404 Not Found
```json
{
  "error": "Context not found"
}
```

### 422 Unprocessable Entity
```json
{
  "error": "Invalid email format"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General API calls**: 100 requests per minute per IP
- **Authentication endpoints**: 10 requests per minute per IP
- **File upload**: 5 requests per minute per user

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Data Models

### User
```json
{
  "id": "integer",
  "username": "string",
  "email": "string (email format)",
  "created_at": "string (ISO 8601 datetime)",
  "is_active": "boolean"
}
```

### Context
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "source_type": "string (files|repo|database)",
  "status": "string (pending|processing|ready|error)",
  "progress": "integer (0-100)",
  "total_chunks": "integer",
  "total_tokens": "integer",
  "config": "object",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

### Message
```json
{
  "id": "integer",
  "role": "string (user|assistant)",
  "content": "string",
  "context_ids": "array of integers",
  "citations": "array of Citation objects",
  "created_at": "string (ISO 8601 datetime)"
}
```

### Citation
```json
{
  "context_name": "string",
  "source": "string",
  "score": "number (0.0-1.0)"
}
```

## WebSocket Events (Real-time Updates)

The API supports WebSocket connections for real-time updates:

### Connection
```javascript
const ws = new WebSocket('ws://localhost:5000/ws');
```

### Events

#### Context Processing Updates
```json
{
  "type": "context_update",
  "context_id": 1,
  "status": "processing",
  "progress": 75,
  "message": "Processing file 3 of 4"
}
```

#### Chat Message Streaming
```json
{
  "type": "chat_stream",
  "session_id": 1,
  "message_id": 2,
  "content": "partial response...",
  "is_complete": false
}
```

## SDK and Client Libraries

### JavaScript/TypeScript
```bash
npm install ragchatbot-api-client
```

```javascript
import { RagChatbotClient } from 'ragchatbot-api-client';

const client = new RagChatbotClient({
  baseUrl: 'http://localhost:5000/api',
  token: 'your-jwt-token'
});

// Create context
const context = await client.contexts.create({
  name: 'My Context',
  source_type: 'files'
});

// Send chat message
const response = await client.chat.query({
  session_id: 1,
  message: 'Hello!',
  context_ids: [context.id]
});
```

### Python
```bash
pip install ragchatbot-api-client
```

```python
from ragchatbot_client import RagChatbotClient

client = RagChatbotClient(
    base_url='http://localhost:5000/api',
    token='your-jwt-token'
)

# Create context
context = client.contexts.create(
    name='My Context',
    source_type='files'
)

# Send chat message
response = client.chat.query(
    session_id=1,
    message='Hello!',
    context_ids=[context.id]
)
```

## Testing

### Using curl
```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Create context (replace TOKEN with actual token)
curl -X POST http://localhost:5000/api/contexts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Context", "source_type": "files"}'
```

### Postman Collection
Import the Postman collection from `/docs/postman_collection.json` for easy API testing.

## Support

For API support and questions:
- **Documentation**: Visit `/api/docs` for interactive documentation
- **Issues**: Report bugs on GitHub
- **Email**: support@ragchatbot.com
