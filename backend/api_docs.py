"""
OpenAPI/Swagger documentation for RAG Chatbot PWA API
"""

from flask import Blueprint, jsonify, render_template_string
from flask_jwt_extended import jwt_required

docs_bp = Blueprint('docs', __name__)

# OpenAPI 3.0 specification
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "RAG Chatbot PWA API",
        "description": "A comprehensive API for the RAG (Retrieval-Augmented Generation) Chatbot Progressive Web Application",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@ragchatbot.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000/api",
            "description": "Development server"
        },
        {
            "url": "https://your-domain.com/api",
            "description": "Production server"
        }
    ],
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        },
        {
            "name": "Contexts",
            "description": "Context management for RAG knowledge bases"
        },
        {
            "name": "Chat",
            "description": "Chat sessions and messaging"
        },
        {
            "name": "Upload",
            "description": "File upload and processing"
        },
        {
            "name": "Admin",
            "description": "Administrative functions and monitoring"
        }
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "username": {"type": "string", "example": "johndoe"},
                    "email": {"type": "string", "format": "email", "example": "john@example.com"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "is_active": {"type": "boolean", "example": True}
                }
            },
            "Context": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "My Project Documentation"},
                    "description": {"type": "string", "example": "Documentation for my software project"},
                    "source_type": {"type": "string", "enum": ["files", "repo", "database"], "example": "files"},
                    "status": {"type": "string", "enum": ["pending", "processing", "ready", "error"], "example": "ready"},
                    "progress": {"type": "integer", "minimum": 0, "maximum": 100, "example": 100},
                    "total_chunks": {"type": "integer", "example": 150},
                    "total_tokens": {"type": "integer", "example": 50000},
                    "config": {"type": "object", "example": {"file_paths": ["README.md", "docs/"]}},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                }
            },
            "ChatSession": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "title": {"type": "string", "example": "Project Discussion"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                    "message_count": {"type": "integer", "example": 5}
                }
            },
            "Message": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "role": {"type": "string", "enum": ["user", "assistant"], "example": "user"},
                    "content": {"type": "string", "example": "What is the main purpose of this project?"},
                    "context_ids": {"type": "array", "items": {"type": "integer"}, "example": [1, 2]},
                    "citations": {"type": "array", "items": {"$ref": "#/components/schemas/Citation"}},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "Citation": {
                "type": "object",
                "properties": {
                    "context_name": {"type": "string", "example": "Project Documentation"},
                    "source": {"type": "string", "example": "README.md"},
                    "score": {"type": "number", "format": "float", "example": 0.95}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Invalid credentials"}
                }
            }
        }
    },
    "paths": {
        "/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register a new user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "email", "password"],
                                "properties": {
                                    "username": {"type": "string", "example": "johndoe"},
                                    "email": {"type": "string", "format": "email", "example": "john@example.com"},
                                    "password": {"type": "string", "minLength": 8, "example": "securepassword123"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User registered successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "access_token": {"type": "string"},
                                        "user": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Login user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "password"],
                                "properties": {
                                    "username": {"type": "string", "example": "johndoe"},
                                    "password": {"type": "string", "example": "securepassword123"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "access_token": {"type": "string"},
                                        "user": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Invalid credentials",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/auth/profile": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get user profile",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "User profile",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "user": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/contexts": {
            "get": {
                "tags": ["Contexts"],
                "summary": "Get all contexts for the authenticated user",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "List of contexts",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "contexts": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Context"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Contexts"],
                "summary": "Create a new context",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name", "source_type"],
                                "properties": {
                                    "name": {"type": "string", "example": "My Project"},
                                    "description": {"type": "string", "example": "Project documentation"},
                                    "source_type": {"type": "string", "enum": ["files", "repo", "database"]},
                                    "config": {"type": "object", "example": {"file_paths": ["README.md"]}}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Context created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "context": {"$ref": "#/components/schemas/Context"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/chat/sessions": {
            "get": {
                "tags": ["Chat"],
                "summary": "Get all chat sessions",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "List of chat sessions",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "sessions": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/ChatSession"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Chat"],
                "summary": "Create a new chat session",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "example": "New Chat"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Chat session created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "session": {"$ref": "#/components/schemas/ChatSession"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/chat/query": {
            "post": {
                "tags": ["Chat"],
                "summary": "Send a chat message",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["session_id", "message"],
                                "properties": {
                                    "session_id": {"type": "integer", "example": 1},
                                    "message": {"type": "string", "example": "What is this project about?"},
                                    "context_ids": {"type": "array", "items": {"type": "integer"}, "example": [1, 2]},
                                    "stream": {"type": "boolean", "example": False}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Chat response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"$ref": "#/components/schemas/Message"},
                                        "citations": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Citation"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@docs_bp.route('/openapi.json')
def openapi_spec():
    """Return the OpenAPI specification as JSON."""
    return jsonify(OPENAPI_SPEC)

@docs_bp.route('/docs')
def swagger_ui():
    """Serve Swagger UI for interactive API documentation."""
    swagger_ui_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Chatbot PWA API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/api/docs/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                });
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(swagger_ui_html)

@docs_bp.route('/redoc')
def redoc():
    """Serve ReDoc for alternative API documentation."""
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Chatbot PWA API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/docs/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return render_template_string(redoc_html)
