"""
Enhanced Context Management Routes - Multi-Source Knowledge Base Creation

This module provides enhanced context creation capabilities supporting multiple
data sources including repositories, documents, web links, and databases.
It includes comprehensive logging, progress tracking, and robust error handling.

Key Features:
- Multi-source context creation (repos, files, links, databases)
- Parallel processing for multiple sources
- Comprehensive validation and error handling
- Detailed logging and progress tracking
- Source-specific configuration and processing
- Mixed-mode contexts with multiple source types

Author: RAG Chatbot Development Team
Version: 2.0.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, List, Any, Optional

# Import models and services
from models import db, Context, User
from services.enhanced_context_service import (
    enhanced_context_service, ContextCreationRequest, SourceConfig
)
from services.detailed_logger import detailed_logger, track_operation
from logging_config import get_logger

# Initialize blueprint and logger
enhanced_contexts_bp = Blueprint('enhanced_contexts', __name__)
logger = get_logger('enhanced_contexts_routes')

def get_current_user_id() -> Optional[int]:
    """Extract user ID from JWT token"""
    try:
        user_id_str = get_jwt_identity()
        return int(user_id_str) if user_id_str else None
    except (ValueError, TypeError):
        return None

@enhanced_contexts_bp.route('/enhanced', methods=['OPTIONS'])
def enhanced_context_options():
    """Handle CORS preflight requests"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,GET,OPTIONS')
    return response

@enhanced_contexts_bp.route('/enhanced', methods=['POST'])
@jwt_required()
def create_enhanced_context():
    """
    Create an enhanced context with multiple data sources
    
    Request Body:
    {
        "name": "My Knowledge Base",
        "description": "Comprehensive knowledge base from multiple sources",
        "sources": [
            {
                "type": "repo",
                "name": "Main Repository",
                "config": {
                    "url": "https://github.com/user/repo.git",
                    "branch": "main",
                    "access_token": "optional_token",
                    "file_extensions": [".py", ".js", ".md"],
                    "exclude_dirs": [".git", "node_modules"]
                },
                "priority": 1,
                "enabled": true
            },
            {
                "type": "files",
                "name": "Documentation Files",
                "config": {
                    "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.docx"],
                    "supported_extensions": [".pdf", ".docx", ".txt"]
                },
                "priority": 2,
                "enabled": true
            },
            {
                "type": "links",
                "name": "Web Documentation",
                "config": {
                    "urls": ["https://docs.example.com/api", "https://wiki.example.com"],
                    "crawl_depth": 1,
                    "follow_links": false
                },
                "priority": 3,
                "enabled": true
            }
        ],
        "chunk_strategy": "language-specific",
        "embedding_model": "text-embedding-004",
        "max_chunk_size": 1000,
        "chunk_overlap": 200,
        "processing_options": {
            "parallel_processing": true,
            "timeout": 300
        }
    }
    """
    client_ip = request.remote_addr
    
    try:
        # Authenticate user
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized enhanced context creation attempt from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Parse request data
        data = request.get_json()
        if not data:
            logger.warning(f"Enhanced context creation with no JSON data from user {user_id}")
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate required fields
        required_fields = ['name', 'sources']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"Enhanced context creation missing fields {missing_fields} from user {user_id}")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Validate sources
        sources_data = data.get('sources', [])
        if not sources_data:
            return jsonify({'error': 'At least one source is required'}), 400
        
        # Parse and validate sources
        sources = []
        for i, source_data in enumerate(sources_data):
            try:
                source = SourceConfig(
                    type=source_data.get('type'),
                    name=source_data.get('name', f'Source {i+1}'),
                    config=source_data.get('config', {}),
                    priority=source_data.get('priority', i+1),
                    enabled=source_data.get('enabled', True)
                )
                
                # Validate source type
                valid_types = ['repo', 'files', 'links', 'database']
                if source.type not in valid_types:
                    return jsonify({
                        'error': f'Invalid source type: {source.type}. Must be one of: {valid_types}'
                    }), 400
                
                # Validate source config
                validation_error = _validate_source_config(source)
                if validation_error:
                    return jsonify({'error': validation_error}), 400
                
                sources.append(source)
                
            except Exception as source_error:
                return jsonify({
                    'error': f'Invalid source configuration at index {i}: {str(source_error)}'
                }), 400
        
        # Create context creation request
        request_obj = ContextCreationRequest(
            name=data['name'],
            description=data.get('description', ''),
            user_id=user_id,
            sources=sources,
            chunk_strategy=data.get('chunk_strategy', 'language-specific'),
            embedding_model=data.get('embedding_model', 'text-embedding-004'),
            max_chunk_size=data.get('max_chunk_size', 1000),
            chunk_overlap=data.get('chunk_overlap', 200),
            processing_options=data.get('processing_options', {})
        )
        
        # Log user activity
        detailed_logger.log_user_activity(
            user_id=user_id,
            session_id=0,  # No session for context creation
            activity_type="enhanced_context_creation",
            details={
                'context_name': request_obj.name,
                'sources_count': len(sources),
                'source_types': [s.type for s in sources],
                'chunk_strategy': request_obj.chunk_strategy,
                'embedding_model': request_obj.embedding_model,
                'client_ip': client_ip
            }
        )
        
        logger.info(f"Creating enhanced context: {request_obj.name} with {len(sources)} sources for user {user_id}")
        
        # Create enhanced context
        result = enhanced_context_service.create_enhanced_context(request_obj)
        
        logger.info(f"Enhanced context creation completed: context_id={result['context_id']} for user {user_id}")
        
        return jsonify({
            'message': 'Enhanced context created successfully',
            'result': result
        }), 201
        
    except Exception as e:
        error_msg = f"Enhanced context creation failed: {str(e)}"
        logger.error(error_msg)
        
        return jsonify({'error': error_msg}), 500

def _validate_source_config(source: SourceConfig) -> Optional[str]:
    """Validate source configuration"""
    
    if source.type == 'repo':
        config = source.config
        if not config.get('url'):
            return f"Repository source '{source.name}' missing required 'url' field"
        
        # Validate URL format
        url = config['url']
        if not (url.startswith('https://') or url.startswith('http://') or url.startswith('git@')):
            return f"Repository source '{source.name}' has invalid URL format"
    
    elif source.type == 'files':
        config = source.config
        file_paths = config.get('file_paths', [])
        if not file_paths:
            return f"Files source '{source.name}' missing required 'file_paths' field"
        
        if not isinstance(file_paths, list):
            return f"Files source '{source.name}' 'file_paths' must be a list"
    
    elif source.type == 'links':
        config = source.config
        urls = config.get('urls', [])
        if not urls:
            return f"Links source '{source.name}' missing required 'urls' field"
        
        if not isinstance(urls, list):
            return f"Links source '{source.name}' 'urls' must be a list"
        
        # Validate URL formats
        for url in urls:
            if not (url.startswith('https://') or url.startswith('http://')):
                return f"Links source '{source.name}' contains invalid URL: {url}"
    
    elif source.type == 'database':
        config = source.config
        if not config.get('connection_string') and not config.get('host'):
            return f"Database source '{source.name}' missing connection configuration"
    
    return None

@enhanced_contexts_bp.route('/enhanced/<int:context_id>/status', methods=['GET'])
@jwt_required()
def get_enhanced_context_status(context_id):
    """Get detailed status of an enhanced context"""
    
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get context
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        # Get detailed status information
        config = context.get_config()
        
        status_info = {
            'context_id': context.id,
            'name': context.name,
            'status': context.status,
            'created_at': context.created_at.isoformat(),
            'updated_at': context.updated_at.isoformat() if context.updated_at else None,
            'source_type': context.source_type,
            'embedding_model': context.embedding_model,
            'vector_store_path': context.vector_store_path,
            'processing_results': config.get('processing_results', {}),
            'sources_info': []
        }
        
        # Add source-specific information
        sources = config.get('sources', [])
        for source in sources:
            source_info = {
                'name': source['name'],
                'type': source['type'],
                'enabled': source['enabled'],
                'priority': source['priority']
            }
            status_info['sources_info'].append(source_info)
        
        return jsonify({'status': status_info}), 200
        
    except Exception as e:
        logger.error(f"Failed to get enhanced context status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@enhanced_contexts_bp.route('/enhanced/templates', methods=['GET'])
@jwt_required()
def get_context_templates():
    """Get predefined context templates for common use cases"""
    
    templates = {
        'software_project': {
            'name': 'Software Project Knowledge Base',
            'description': 'Complete knowledge base for a software project including code and documentation',
            'sources': [
                {
                    'type': 'repo',
                    'name': 'Main Repository',
                    'config': {
                        'url': 'https://github.com/user/project.git',
                        'branch': 'main',
                        'file_extensions': ['.py', '.js', '.java', '.cpp', '.md', '.txt'],
                        'exclude_dirs': ['.git', 'node_modules', '__pycache__', 'build', 'dist']
                    },
                    'priority': 1,
                    'enabled': True
                },
                {
                    'type': 'links',
                    'name': 'Documentation Sites',
                    'config': {
                        'urls': ['https://docs.project.com'],
                        'crawl_depth': 2
                    },
                    'priority': 2,
                    'enabled': True
                }
            ],
            'chunk_strategy': 'language-specific',
            'embedding_model': 'text-embedding-004'
        },
        'research_project': {
            'name': 'Research Project Knowledge Base',
            'description': 'Academic research project with papers, data, and documentation',
            'sources': [
                {
                    'type': 'files',
                    'name': 'Research Papers',
                    'config': {
                        'file_paths': [],
                        'supported_extensions': ['.pdf', '.docx', '.txt', '.md']
                    },
                    'priority': 1,
                    'enabled': True
                },
                {
                    'type': 'links',
                    'name': 'Online Resources',
                    'config': {
                        'urls': [],
                        'crawl_depth': 1
                    },
                    'priority': 2,
                    'enabled': True
                }
            ],
            'chunk_strategy': 'semantic',
            'embedding_model': 'text-embedding-004'
        },
        'documentation_hub': {
            'name': 'Documentation Hub',
            'description': 'Centralized documentation from multiple sources',
            'sources': [
                {
                    'type': 'repo',
                    'name': 'Documentation Repository',
                    'config': {
                        'url': 'https://github.com/user/docs.git',
                        'branch': 'main',
                        'file_extensions': ['.md', '.rst', '.txt'],
                        'exclude_dirs': ['.git', '_build']
                    },
                    'priority': 1,
                    'enabled': True
                },
                {
                    'type': 'files',
                    'name': 'Additional Documents',
                    'config': {
                        'file_paths': [],
                        'supported_extensions': ['.pdf', '.docx', '.md']
                    },
                    'priority': 2,
                    'enabled': True
                },
                {
                    'type': 'links',
                    'name': 'Online Documentation',
                    'config': {
                        'urls': [],
                        'crawl_depth': 1
                    },
                    'priority': 3,
                    'enabled': True
                }
            ],
            'chunk_strategy': 'language-specific',
            'embedding_model': 'text-embedding-004'
        }
    }
    
    return jsonify({'templates': templates}), 200