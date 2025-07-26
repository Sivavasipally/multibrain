# RAG Chatbot API Reference

## 🔗 **Base URL**
```
http://localhost:5000/api
```

## 🔐 **Authentication**
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 📋 **Authentication Endpoints**

### **POST /auth/register**
Register a new user account.

**Request:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123"
}
```

**Response (201):**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "is_active": true
    }
}
```

**Error Responses:**
- `400`: Invalid input data
- `409`: Username or email already exists

### **POST /auth/login**
Authenticate user and receive access token.

**Request:**
```json
{
    "username": "john_doe",
    "password": "secure_password123"
}
```

**Response (200):**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
    }
}
```

**Error Responses:**
- `401`: Invalid credentials
- `400`: Missing username or password

### **POST /auth/logout**
Logout user (invalidate token).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "message": "Successfully logged out"
}
```

---

## 📁 **Context Management Endpoints**

### **GET /contexts**
Retrieve all contexts for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10)
- `status` (optional): Filter by status (pending, processing, ready, error)

**Response (200):**
```json
{
    "contexts": [
        {
            "id": 1,
            "name": "Research Papers",
            "description": "Academic research documents",
            "source_type": "files",
            "chunk_strategy": "language-specific",
            "embedding_model": "text-embedding-004",
            "status": "ready",
            "progress": 100,
            "total_chunks": 150,
            "total_tokens": 50000,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 1,
        "pages": 1
    }
}
```

### **POST /contexts**
Create a new context.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
    "name": "Research Papers",
    "description": "Academic research documents",
    "source_type": "files",
    "chunk_strategy": "language-specific",
    "embedding_model": "text-embedding-004",
    "config": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "custom_settings": {}
    }
}
```

**Response (201):**
```json
{
    "message": "Context created successfully",
    "context": {
        "id": 1,
        "name": "Research Papers",
        "description": "Academic research documents",
        "source_type": "files",
        "chunk_strategy": "language-specific",
        "embedding_model": "text-embedding-004",
        "status": "pending",
        "progress": 0,
        "created_at": "2024-01-01T00:00:00Z"
    }
}
```

**Error Responses:**
- `400`: Invalid input data
- `409`: Context name already exists for user

### **GET /contexts/{id}**
Get detailed information about a specific context.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "context": {
        "id": 1,
        "name": "Research Papers",
        "description": "Academic research documents",
        "source_type": "files",
        "chunk_strategy": "language-specific",
        "embedding_model": "text-embedding-004",
        "status": "ready",
        "progress": 100,
        "total_chunks": 150,
        "total_tokens": 50000,
        "error_message": null,
        "config": {
            "chunk_strategy": "language-specific",
            "embedding_model": "text-embedding-004",
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "documents": [
            {
                "id": 1,
                "filename": "20240101_120000_research_paper.pdf",
                "original_filename": "research_paper.pdf",
                "file_size": 1024000,
                "file_type": "application/pdf",
                "upload_date": "2024-01-01T00:00:00Z",
                "processing_status": "completed"
            }
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T01:00:00Z"
    }
}
```

**Error Responses:**
- `404`: Context not found
- `403`: Access denied (not owner)

### **PUT /contexts/{id}**
Update context information.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
    "name": "Updated Research Papers",
    "description": "Updated description",
    "config": {
        "custom_setting": "value"
    }
}
```

**Response (200):**
```json
{
    "message": "Context updated successfully",
    "context": {
        "id": 1,
        "name": "Updated Research Papers",
        "description": "Updated description",
        "updated_at": "2024-01-01T02:00:00Z"
    }
}
```

### **DELETE /contexts/{id}**
Delete a context and all associated data.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "message": "Context 'Research Papers' deleted successfully",
    "cleanup_stats": {
        "vector_stores_deleted": 1,
        "documents_deleted": 5,
        "files_deleted": 1,
        "chunks_deleted": 150
    }
}
```

**Error Responses:**
- `404`: Context not found
- `403`: Access denied (not owner)

### **GET /contexts/{id}/chunks**
Get text chunks for a context.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `search` (optional): Search within chunk content

**Response (200):**
```json
{
    "chunks": [
        {
            "id": 1,
            "context_id": 1,
            "file_name": "research_paper.pdf",
            "chunk_index": 0,
            "content": "This is the content of the first chunk...",
            "metadata": {
                "file_type": ".pdf",
                "chunk_size": 1000,
                "chunk_strategy": "language-specific"
            },
            "created_at": "2024-01-01T00:30:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 150,
        "pages": 8
    }
}
```

---

## 📤 **File Upload Endpoints**

### **POST /upload/files**
Upload files to a context for processing.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `files`: File or array of files
- `context_id`: Integer (required)

**Supported File Types:**
- PDF (.pdf)
- Word Documents (.docx)
- Excel Files (.xlsx)
- Text Files (.txt)
- Markdown Files (.md)

**Response (200):**
```json
{
    "message": "Files uploaded and processed successfully",
    "files_processed": 3,
    "total_chunks": 45,
    "processing_time": 12.5,
    "files": [
        {
            "filename": "document1.pdf",
            "size": 1024000,
            "chunks_created": 15,
            "status": "completed"
        },
        {
            "filename": "document2.docx",
            "size": 512000,
            "chunks_created": 10,
            "status": "completed"
        }
    ]
}
```

**Error Responses:**
- `400`: Invalid file type or size
- `404`: Context not found
- `413`: File too large
- `422`: Processing failed

### **GET /upload/status/{context_id}**
Check upload and processing status for a context.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "context_id": 1,
    "status": "processing",
    "progress": 75,
    "files_total": 5,
    "files_processed": 3,
    "files_pending": 2,
    "estimated_completion": "2024-01-01T01:15:00Z",
    "current_file": "large_document.pdf"
}
```

---

## 💬 **Chat Endpoints**

### **POST /chat/query**
Send a chat query with context-aware response.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
    "message": "What are the main findings in the research papers?",
    "context_ids": [1, 2],
    "session_id": 1,
    "model": "gemini-pro",
    "max_tokens": 500,
    "temperature": 0.7
}
```

**Response (200):**
```json
{
    "response": "Based on the research documents, the main findings are...",
    "citations": [
        {
            "document": "research_paper.pdf",
            "chunk": "The study demonstrates that...",
            "relevance_score": 0.95,
            "page": 3
        },
        {
            "document": "analysis.docx",
            "chunk": "Furthermore, the data shows...",
            "relevance_score": 0.87,
            "page": 1
        }
    ],
    "tokens_used": 150,
    "model_used": "gemini-pro",
    "processing_time": 2.3,
    "context_chunks_used": 5
}
```

**Error Responses:**
- `400`: Invalid request parameters
- `404`: Context or session not found
- `429`: Rate limit exceeded
- `503`: AI service unavailable

### **GET /chat/sessions**
Get chat sessions for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10)

**Response (200):**
```json
{
    "sessions": [
        {
            "id": 1,
            "title": "Research Discussion",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z",
            "message_count": 10,
            "last_message": "What are the implications of these findings?"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 5,
        "pages": 1
    }
}
```

### **POST /chat/sessions**
Create a new chat session.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
    "title": "New Research Discussion"
}
```

**Response (201):**
```json
{
    "message": "Chat session created successfully",
    "session": {
        "id": 2,
        "title": "New Research Discussion",
        "created_at": "2024-01-01T02:00:00Z",
        "message_count": 0
    }
}
```

### **GET /chat/sessions/{id}/messages**
Get messages for a specific chat session.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50)

**Response (200):**
```json
{
    "messages": [
        {
            "id": 1,
            "session_id": 1,
            "role": "user",
            "content": "What are the main findings in the research?",
            "context_ids": [1],
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "session_id": 1,
            "role": "assistant",
            "content": "Based on the research documents, the main findings are...",
            "citations": [...],
            "tokens_used": 150,
            "model_used": "gemini-pro",
            "created_at": "2024-01-01T00:01:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 50,
        "total": 10,
        "pages": 1
    }
}
```

### **DELETE /chat/sessions/{id}**
Delete a chat session and all its messages.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
    "message": "Chat session deleted successfully"
}
```

---

## 🔧 **System Endpoints**

### **GET /health**
Check application health status.

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "uptime": 3600,
    "database": "connected",
    "services": {
        "llm_service": "available",
        "vector_service": "available",
        "embedding_service": "available"
    }
}
```

### **GET /health/detailed**
Detailed system health information.

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "system": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 23.1,
        "load_average": [1.2, 1.1, 1.0]
    },
    "database": {
        "status": "connected",
        "total_users": 50,
        "total_contexts": 200,
        "total_documents": 1000,
        "total_chunks": 50000
    },
    "services": {
        "llm_service": {
            "status": "available",
            "response_time": 0.5,
            "last_check": "2024-01-01T00:00:00Z"
        },
        "vector_service": {
            "status": "available",
            "index_size": 50000,
            "last_update": "2024-01-01T00:00:00Z"
        }
    }
}
```

---

## 📊 **Admin Endpoints**

### **GET /admin/dashboard**
Get admin dashboard data (admin users only).

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200):**
```json
{
    "system_stats": {
        "total_users": 50,
        "active_users": 35,
        "total_contexts": 200,
        "total_documents": 1000,
        "total_chunks": 50000,
        "storage_used": "2.5 GB"
    },
    "performance_metrics": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 23.1,
        "response_time_avg": 0.8
    },
    "recent_activity": [
        {
            "user": "john_doe",
            "action": "uploaded_file",
            "context": "Research Papers",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ],
    "error_logs": [
        {
            "level": "ERROR",
            "message": "Failed to process document",
            "timestamp": "2024-01-01T00:00:00Z",
            "user": "jane_doe"
        }
    ]
}
```

### **GET /admin/users**
Get user management data (admin only).

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `search` (optional): Search by username or email

**Response (200):**
```json
{
    "users": [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "is_active": true,
            "last_login": "2024-01-01T12:00:00Z",
            "context_count": 5,
            "document_count": 25
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 50,
        "pages": 3
    }
}
```

---

## 🚨 **Error Codes**

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 | Bad Request | Invalid input data, missing required fields |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions, not resource owner |
| 404 | Not Found | Resource doesn't exist or user doesn't have access |
| 409 | Conflict | Resource already exists (username, email, context name) |
| 413 | Payload Too Large | File size exceeds maximum allowed |
| 422 | Unprocessable Entity | Valid format but processing failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error, check logs |
| 503 | Service Unavailable | External service (AI, database) unavailable |

---

## 📝 **Rate Limiting**

| Endpoint Category | Rate Limit | Window |
|------------------|------------|---------|
| Authentication | 5 requests | 1 minute |
| File Upload | 10 requests | 5 minutes |
| Chat Queries | 60 requests | 1 minute |
| General API | 100 requests | 1 minute |
| Admin Endpoints | 200 requests | 1 minute |

---

**API Version**: 1.0  
**Last Updated**: 2024-01-01  
**Base URL**: `http://localhost:5000/api`
