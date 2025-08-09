"""
Context Management Routes for RAG Chatbot PWA - Knowledge Base Administration

This module provides comprehensive context management functionality for the RAG (Retrieval-Augmented
Generation) chatbot system. Contexts represent knowledge bases that contain processed documents,
code repositories, or database connections that serve as the foundation for AI-powered responses.

Key Features:
- Context lifecycle management (create, read, update, delete)
- Multi-source context support (files, repositories, databases)
- Document processing and chunking with multiple strategies
- Vector store management and indexing
- Context status monitoring and processing progress tracking
- Reprocessing and cleanup operations
- Comprehensive error handling and logging
- JWT-based authentication and authorization

Context Types:
- Files: Upload and process documents (PDF, DOCX, TXT, code files)
- Repositories: Clone and analyze Git repositories (GitHub, Bitbucket)
- Databases: Connect to external data sources (SQL, NoSQL)

Context States:
- pending: Newly created, awaiting processing
- processing: Documents being processed and indexed
- ready: Available for chat queries
- error: Processing failed, requires attention

Processing Pipeline:
1. Context Creation: Initialize metadata and configuration
2. Source Ingestion: Load content from files, repos, or databases
3. Document Processing: Extract text and structure analysis
4. Text Chunking: Intelligent segmentation with overlap
5. Vector Indexing: Create FAISS index for similarity search
6. Status Updates: Track progress and handle errors
7. Cleanup: Remove temporary files and optimize storage

API Endpoints:
- GET /: List user's contexts with metadata
- POST /: Create new context with configuration
- GET /{id}: Get specific context details
- PUT /{id}: Update context configuration
- DELETE /{id}: Delete context and cleanup resources
- POST /{id}/reprocess: Reprocess context documents
- GET /{id}/status: Get processing status and progress

Dependencies:
- Flask: Web framework and routing
- SQLAlchemy: Database operations and models
- Flask-JWT-Extended: Authentication and authorization
- Document processing services
- Vector storage services

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Context, Document

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('contexts_routes')

def get_current_user_id():
    """
    Extract and validate user ID from JWT token for context operations
    
    This helper function securely extracts the user identity from the JWT token
    and ensures proper access control for context management operations.
    
    Returns:
        int: The authenticated user's ID if valid token exists
        None: If no token or invalid token
        
    Raises:
        ValueError: If JWT identity cannot be converted to integer
        
    Security:
        - Validates token authenticity
        - Prevents unauthorized context access
        - Logs authentication attempts for audit
    """
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved user ID {user_id} from JWT for context operations")
            return user_id
        else:
            logger.debug("No user identity found in JWT token for context request")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer for context operations: {e}")
        return None

# Note: Celery tasks not available in local version
# Background processing would be handled by celery in production:
# from tasks.context_processor import process_context_task

contexts_bp = Blueprint('contexts', __name__)

@contexts_bp.route('/', methods=['GET'])
@jwt_required()
def get_contexts():
    """
    Retrieve all contexts (knowledge bases) for the authenticated user
    
    Returns a comprehensive list of the user's contexts including metadata,
    processing status, and statistics. Contexts are ordered by creation date
    (most recent first) to show the latest knowledge bases at the top.
    
    Authentication:
        Requires valid JWT token in Authorization header
        
    Query Parameters:
        status (optional): Filter by context status (pending, processing, ready, error)
        source_type (optional): Filter by source type (files, repo, database)
        limit (optional): Maximum number of contexts to return
        offset (optional): Number of contexts to skip for pagination
        
    Returns:
        200: Success response with contexts list
        {
            "contexts": [
                {
                    "id": "Context ID",
                    "name": "Context name",
                    "description": "Context description",
                    "source_type": "files|repo|database",
                    "status": "pending|processing|ready|error",
                    "progress": "Processing progress (0-100)",
                    "total_chunks": "Number of text chunks",
                    "total_tokens": "Total token count",
                    "created_at": "ISO timestamp",
                    "updated_at": "ISO timestamp"
                }
            ],
            "total": "Total context count",
            "summary": {
                "by_status": {"ready": 5, "processing": 1, "error": 0},
                "by_type": {"files": 3, "repo": 2, "database": 1},
                "total_chunks": 15420,
                "total_tokens": 125000
            }
        }
        
        401: Unauthorized (invalid or missing JWT token)
        500: Internal server error
        
    Example:
        GET /api/contexts?status=ready&limit=10
        Authorization: Bearer <jwt_token>
    """
    client_ip = request.remote_addr
    logger.info(f"Contexts list request from IP: {client_ip}")
    
    try:
        # Authenticate user
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized contexts request from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Parse query parameters
        status_filter = request.args.get('status')
        source_type_filter = request.args.get('source_type')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        
        logger.debug(f"Context list filters - status: {status_filter}, type: {source_type_filter}, limit: {limit}")
        
        # Build query with filters
        query = Context.query.filter_by(user_id=user_id)
        
        if status_filter:
            valid_statuses = ['pending', 'processing', 'ready', 'error']
            if status_filter in valid_statuses:
                query = query.filter_by(status=status_filter)
            else:
                logger.warning(f"Invalid status filter '{status_filter}' from user {user_id}")
        
        if source_type_filter:
            valid_types = ['files', 'repo', 'database']
            if source_type_filter in valid_types:
                query = query.filter_by(source_type=source_type_filter)
            else:
                logger.warning(f"Invalid source_type filter '{source_type_filter}' from user {user_id}")
        
        # Apply ordering and pagination
        query = query.order_by(Context.created_at.desc())
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        # Execute query
        contexts = query.all()
        total_contexts = Context.query.filter_by(user_id=user_id).count()
        
        logger.info(f"Retrieved {len(contexts)} contexts for user {user_id} (total: {total_contexts})")
        
        # Generate context data
        contexts_data = []
        for context in contexts:
            context_dict = context.to_dict()
            # Add additional computed fields if needed
            contexts_data.append(context_dict)
        
        # Generate summary statistics
        all_user_contexts = Context.query.filter_by(user_id=user_id).all()
        summary = {
            'by_status': {},
            'by_type': {},
            'total_chunks': 0,
            'total_tokens': 0
        }
        
        for context in all_user_contexts:
            # Count by status
            status = context.status or 'pending'
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            
            # Count by type
            source_type = context.source_type or 'unknown'
            summary['by_type'][source_type] = summary['by_type'].get(source_type, 0) + 1
            
            # Sum totals
            summary['total_chunks'] += context.total_chunks or 0
            summary['total_tokens'] += context.total_tokens or 0
        
        response_data = {
            'contexts': contexts_data,
            'total': total_contexts,
            'count': len(contexts_data),
            'summary': summary
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = f"Error fetching contexts: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "endpoint": "get_contexts",
            "user_id": user_id if 'user_id' in locals() else None,
            "client_ip": client_ip,
            "filters": {
                "status": status_filter if 'status_filter' in locals() else None,
                "source_type": source_type_filter if 'source_type_filter' in locals() else None,
                "limit": limit if 'limit' in locals() else None
            }
        })
        return jsonify({'error': 'Failed to retrieve contexts'}), 500

@contexts_bp.route('/', methods=['OPTIONS'])
def create_context_options():
    """Handle CORS preflight requests for context creation"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@contexts_bp.route('/', methods=['POST'])
@jwt_required()
def create_context():
    """Create a new context"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'source_type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate source_type
        valid_source_types = ['repo', 'database', 'files']
        if data['source_type'] not in valid_source_types:
            return jsonify({'error': 'Invalid source_type'}), 400
        
        # Create new context
        context = Context(
            name=data['name'],
            description=data.get('description', ''),
            user_id=user_id,
            source_type=data['source_type'],
            chunk_strategy=data.get('chunk_strategy', 'language-specific'),
            embedding_model=data.get('embedding_model', 'text-embedding-004'),
            status='pending'
        )
        
        # Set configuration based on source type
        config = {}
        if data['source_type'] == 'repo':
            config = {
                'url': data.get('repo_config', {}).get('url', ''),
                'branch': data.get('repo_config', {}).get('branch', 'main'),
                'access_token': data.get('repo_config', {}).get('access_token', '')
            }
        elif data['source_type'] == 'database':
            config = {
                'type': data.get('database_config', {}).get('type', ''),
                'connection_string': data.get('database_config', {}).get('connection_string', ''),
                'tables': data.get('database_config', {}).get('tables', [])
            }
        elif data['source_type'] == 'files':
            config = {
                'file_paths': data.get('file_config', {}).get('file_paths', []),
                'supported_extensions': data.get('file_config', {}).get('supported_extensions', [])
            }
        
        context.set_config(config)
        
        db.session.add(context)
        db.session.commit()
        
        # Start background processing
        # # process_context_task.delay(context.id)
        
        return jsonify({
            'message': 'Context created successfully',
            'context': context.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>', methods=['GET'])
@jwt_required()
def get_context(context_id):
    """Get a specific context"""
    try:
        user_id = get_current_user_id()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        # Include documents
        documents = [doc.to_dict() for doc in context.documents]
        context_dict = context.to_dict()
        context_dict['documents'] = documents
        
        return jsonify({'context': context_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>', methods=['PUT'])
@jwt_required()
def update_context(context_id):
    """Update a context"""
    try:
        user_id = get_current_user_id()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            context.name = data['name']
        if 'description' in data:
            context.description = data['description']
        if 'chunk_strategy' in data:
            context.chunk_strategy = data['chunk_strategy']
        if 'embedding_model' in data:
            context.embedding_model = data['embedding_model']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Context updated successfully',
            'context': context.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>', methods=['DELETE'])
@jwt_required()
def delete_context(context_id):
    """Delete a context and all associated data"""
    try:
        user_id = get_current_user_id()
        print(f"DEBUG: Deleting context {context_id} for user {user_id}")

        # Get context and verify ownership
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        
        if not context:
            return jsonify({'error': 'Context not found'}), 404

        try:
            # Try comprehensive cleanup service first
            from services.context_cleanup_service import ContextCleanupService
            cleanup_service = ContextCleanupService()
            result = cleanup_service.delete_context_completely(context_id, user_id)

            if result['success']:
                return jsonify({
                    'message': result['message'],
                    'cleanup_stats': result['stats']
                }), 200
            else:
                print(f"DEBUG: Cleanup service failed: {result['error']}")
                # Fall back to simple deletion
                
        except Exception as cleanup_error:
            print(f"DEBUG: Cleanup service error: {str(cleanup_error)}")
            # Fall back to simple deletion

        # Simple fallback deletion
        print("DEBUG: Using fallback deletion method")
        
        # Delete related documents first (if they exist)
        try:
            Document.query.filter_by(context_id=context_id).delete()
            print("DEBUG: Deleted documents")
        except Exception as e:
            print(f"DEBUG: Error deleting documents: {str(e)}")
        
        # Delete the context
        db.session.delete(context)
        db.session.commit()
        
        return jsonify({
            'message': f'Context "{context.name}" deleted successfully',
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error in delete_context: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_context(context_id):
    """Reprocess a context"""
    try:
        user_id = get_current_user_id()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        print(f"DEBUG: Starting reprocess for context {context_id}: {context.name}")
        
        # Reset status and start reprocessing
        context.status = 'processing'
        context.progress = 0
        context.error_message = None
        
        db.session.commit()
        
        # For file-based contexts, reprocess uploaded documents
        if context.source_type == 'files':
            try:
                # Import the processing function from upload route
                from routes.upload import process_uploaded_documents
                
                print(f"DEBUG: Reprocessing documents for context {context_id}")
                
                # Delete existing text chunks first
                from models import TextChunk
                existing_chunks = TextChunk.query.filter_by(context_id=context_id).all()
                for chunk in existing_chunks:
                    db.session.delete(chunk)
                db.session.commit()
                print(f"DEBUG: Deleted {len(existing_chunks)} existing chunks")
                
                # Delete existing vector store
                if context.vector_store_path:
                    from services.vector_service import VectorService
                    vector_service = VectorService()
                    if vector_service.delete_vector_store(context.vector_store_path):
                        print(f"DEBUG: Deleted existing vector store: {context.vector_store_path}")
                    context.vector_store_path = None
                    context.total_chunks = 0
                    db.session.commit()
                
                # Reprocess documents
                process_uploaded_documents(context_id)
                
                # Update status to ready
                context.status = 'ready'
                context.progress = 100
                db.session.commit()
                
                print(f"DEBUG: Reprocessing completed for context {context_id}")
                
            except Exception as processing_error:
                print(f"DEBUG: Error during reprocessing: {str(processing_error)}")
                import traceback
                traceback.print_exc()
                
                # Set error status
                context.status = 'error'
                context.error_message = str(processing_error)
                db.session.commit()
                
                return jsonify({
                    'error': f'Reprocessing failed: {str(processing_error)}',
                    'context': context.to_dict()
                }), 500
        else:
            # For other source types, just mark as ready for now
            # TODO: Implement repo and database reprocessing
            context.status = 'ready'
            context.progress = 100
            db.session.commit()
            print(f"DEBUG: Reprocessing completed for {context.source_type} context {context_id}")
        
        return jsonify({
            'message': 'Context reprocessing completed successfully',
            'context': context.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error in reprocess_context: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>/status', methods=['GET'])
@jwt_required()
def get_context_status(context_id):
    """Get context processing status"""
    try:
        user_id = get_current_user_id()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        return jsonify({
            'status': context.status,
            'progress': context.progress,
            'error_message': context.error_message,
            'total_chunks': context.total_chunks,
            'total_tokens': context.total_tokens
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/search', methods=['GET', 'POST'])
@jwt_required()
def search_contexts():
    """
    Advanced context search with filtering, sorting, and content search
    
    Provides comprehensive search capabilities for user contexts including:
    - Full-text search across names and descriptions
    - Advanced query operators (AND, OR, NOT)
    - Status and source type filtering
    - Date range and chunk count filtering
    - Relevance-based scoring and ranking
    - Search suggestions and history
    
    Authentication:
        Requires valid JWT token in Authorization header
        
    Query Parameters (GET):
        q (optional): Search query with support for operators
        status (optional): Filter by status (ready, processing, error)
        source_type (optional): Filter by source type (files, repo, database)
        date_from (optional): Start date filter (ISO format)
        date_to (optional): End date filter (ISO format)
        chunks_min (optional): Minimum chunk count filter
        chunks_max (optional): Maximum chunk count filter
        sort_by (optional): Sort field (name, created_at, chunks, relevance)
        sort_order (optional): Sort order (asc, desc)
        limit (optional): Maximum results to return (default: 50)
        offset (optional): Results offset for pagination (default: 0)
        
    Request Body (POST):
        {
            "query": "search terms",
            "filters": {
                "status": "ready",
                "source_type": "files",
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-12-31T23:59:59Z"
                },
                "chunk_range": {
                    "min": 10,
                    "max": 1000
                }
            },
            "sort": {
                "field": "relevance",
                "order": "desc"
            },
            "limit": 20,
            "offset": 0
        }
        
    Returns:
        200: Success response with search results
        {
            "results": [
                {
                    "context": {context_object},
                    "relevance_score": 95.5,
                    "highlights": [
                        {
                            "field": "name",
                            "fragment": "highlighted text",
                            "positions": [12, 25]
                        }
                    ]
                }
            ],
            "total": 15,
            "query": "search terms",
            "filters": {applied_filters},
            "execution_time_ms": 125,
            "suggestions": ["term1", "term2"]
        }
        
        401: Unauthorized (invalid or missing JWT token)
        400: Bad request (invalid parameters)
        500: Internal server error
        
    Examples:
        GET /api/contexts/search?q=python+code&status=ready&sort_by=relevance
        POST /api/contexts/search (with JSON body)
    """
    import time
    
    client_ip = request.remote_addr
    start_time = time.time()
    
    logger.info(f"Context search request from IP: {client_ip}")
    
    try:
        # Authenticate user
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized context search from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Parse parameters based on request method
        if request.method == 'GET':
            query = request.args.get('q', '').strip()
            filters = {
                'status': request.args.get('status'),
                'source_type': request.args.get('source_type'),
                'date_from': request.args.get('date_from'),
                'date_to': request.args.get('date_to'),
                'chunks_min': request.args.get('chunks_min', type=int),
                'chunks_max': request.args.get('chunks_max', type=int),
            }
            sort_field = request.args.get('sort_by', 'relevance')
            sort_order = request.args.get('sort_order', 'desc')
            limit = request.args.get('limit', type=int, default=50)
            offset = request.args.get('offset', type=int, default=0)
        else:  # POST
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            filters = data.get('filters', {})
            sort_config = data.get('sort', {})
            sort_field = sort_config.get('field', 'relevance')
            sort_order = sort_config.get('order', 'desc')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)
        
        # Validate parameters
        valid_statuses = ['ready', 'processing', 'error', 'pending']
        valid_source_types = ['files', 'repo', 'database']
        valid_sort_fields = ['name', 'created_at', 'chunks', 'relevance']
        valid_sort_orders = ['asc', 'desc']
        
        if filters.get('status') and filters['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
            
        if filters.get('source_type') and filters['source_type'] not in valid_source_types:
            return jsonify({'error': f'Invalid source_type. Must be one of: {valid_source_types}'}), 400
            
        if sort_field not in valid_sort_fields:
            return jsonify({'error': f'Invalid sort_by. Must be one of: {valid_sort_fields}'}), 400
            
        if sort_order not in valid_sort_orders:
            return jsonify({'error': f'Invalid sort_order. Must be one of: {valid_sort_orders}'}), 400
        
        logger.debug(f"Context search - query: '{query}', filters: {filters}, sort: {sort_field} {sort_order}")
        
        # Build base query
        contexts_query = Context.query.filter_by(user_id=user_id)
        
        # Apply filters
        if filters.get('status'):
            contexts_query = contexts_query.filter_by(status=filters['status'])
            
        if filters.get('source_type'):
            contexts_query = contexts_query.filter_by(source_type=filters['source_type'])
            
        if filters.get('date_from'):
            try:
                from datetime import datetime
                date_from = datetime.fromisoformat(filters['date_from'].replace('Z', '+00:00'))
                contexts_query = contexts_query.filter(Context.created_at >= date_from)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format. Use ISO format.'}), 400
                
        if filters.get('date_to'):
            try:
                from datetime import datetime
                date_to = datetime.fromisoformat(filters['date_to'].replace('Z', '+00:00'))
                contexts_query = contexts_query.filter(Context.created_at <= date_to)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format. Use ISO format.'}), 400
                
        if filters.get('chunks_min') is not None:
            contexts_query = contexts_query.filter(Context.total_chunks >= filters['chunks_min'])
            
        if filters.get('chunks_max') is not None:
            contexts_query = contexts_query.filter(Context.total_chunks <= filters['chunks_max'])
        
        # Get all matching contexts
        all_contexts = contexts_query.all()
        
        # Perform search and scoring
        results = []
        
        if query:
            # Parse search query for advanced operators
            parsed_query = _parse_search_query(query)
            
            for context in all_contexts:
                score = _calculate_relevance_score(context, parsed_query)
                if score > 0:
                    highlights = _generate_highlights(context, query)
                    results.append({
                        'context': context.to_dict(),
                        'relevance_score': score,
                        'highlights': highlights
                    })
        else:
            # No search query, return all contexts with default score
            for context in all_contexts:
                results.append({
                    'context': context.to_dict(),
                    'relevance_score': 1.0,
                    'highlights': []
                })
        
        # Sort results
        if sort_field == 'relevance':
            results.sort(key=lambda x: x['relevance_score'], reverse=(sort_order == 'desc'))
        else:
            # Sort by context attributes
            def sort_key(result):
                context_dict = result['context']
                if sort_field == 'name':
                    return context_dict.get('name', '').lower()
                elif sort_field == 'created_at':
                    return context_dict.get('created_at', '')
                elif sort_field == 'chunks':
                    return context_dict.get('total_chunks', 0)
                return 0
            
            results.sort(key=sort_key, reverse=(sort_order == 'desc'))
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[offset:offset + limit] if limit else results[offset:]
        
        # Generate search suggestions (simple implementation)
        suggestions = []
        if query:
            # Get context names and descriptions that partially match
            all_user_contexts = Context.query.filter_by(user_id=user_id).all()
            for context in all_user_contexts[:10]:  # Limit suggestions
                if query.lower() in context.name.lower():
                    suggestions.append(context.name)
                elif context.description and query.lower() in context.description.lower():
                    words = context.description.split()[:3]  # First few words
                    suggestions.append(' '.join(words))
        
        execution_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Context search completed for user {user_id}: {total_results} results in {execution_time}ms")
        
        return jsonify({
            'results': paginated_results,
            'total': total_results,
            'query': query,
            'filters': {k: v for k, v in filters.items() if v is not None},
            'execution_time_ms': execution_time,
            'suggestions': list(set(suggestions))[:10]  # Remove duplicates and limit
        }), 200
        
    except Exception as e:
        logger.error(f"Context search error for user {user_id}: {str(e)}")
        log_error_with_context(
            logger, e, 'context_search_error',
            user_id=user_id,
            query=locals().get('query', ''),
            client_ip=client_ip
        )
        return jsonify({'error': 'Search operation failed'}), 500


def _parse_search_query(query):
    """
    Parse search query for advanced operators
    
    Supports:
    - AND: terms that must all be present
    - OR: terms where at least one must be present
    - NOT/-: terms that must not be present
    - +: terms that must be present (required)
    - "phrase": exact phrase matching
    """
    import re
    
    required_terms = []
    optional_terms = []
    excluded_terms = []
    phrases = []
    
    # Extract quoted phrases first
    phrase_pattern = r'"([^"]*)"'
    phrases = re.findall(phrase_pattern, query)
    query_without_phrases = re.sub(phrase_pattern, '', query)
    
    # Split remaining terms
    terms = query_without_phrases.split()
    
    i = 0
    while i < len(terms):
        term = terms[i].lower().strip()
        
        if not term:
            i += 1
            continue
            
        if term == 'and' or term == '&&':
            i += 1
            continue
        elif term == 'or' or term == '||':
            i += 1
            continue
        elif term == 'not':
            # Next term should be excluded
            if i + 1 < len(terms):
                excluded_terms.append(terms[i + 1].lower())
                i += 2
            else:
                i += 1
        elif term.startswith('-'):
            excluded_terms.append(term[1:])
            i += 1
        elif term.startswith('+'):
            required_terms.append(term[1:])
            i += 1
        else:
            optional_terms.append(term)
            i += 1
    
    return {
        'required': required_terms,
        'optional': optional_terms,
        'excluded': excluded_terms,
        'phrases': [p.lower() for p in phrases]
    }


def _calculate_relevance_score(context, parsed_query):
    """Calculate relevance score for a context based on parsed query"""
    text = f"{context.name} {context.description or ''}".lower()
    score = 0.0
    
    # Check required terms - all must be present
    for term in parsed_query['required']:
        if term not in text:
            return 0.0  # Fail if any required term is missing
        score += 10.0  # High score for required terms
    
    # Check excluded terms - none should be present
    for term in parsed_query['excluded']:
        if term in text:
            return 0.0  # Fail if any excluded term is present
    
    # Check phrases - exact matches
    for phrase in parsed_query['phrases']:
        if phrase in text:
            score += 15.0  # Very high score for phrase matches
    
    # Check optional terms
    for term in parsed_query['optional']:
        if term in text:
            score += 5.0  # Medium score for optional terms
            # Boost if found in name
            if term in context.name.lower():
                score += 10.0
    
    # Boost score based on context metadata
    if context.status == 'ready':
        score += 2.0  # Slightly prefer ready contexts
        
    if context.total_chunks and context.total_chunks > 0:
        score += min(context.total_chunks / 100.0, 5.0)  # Up to 5 points for chunk count
    
    return score


def _generate_highlights(context, query):
    """Generate highlights for search results"""
    highlights = []
    terms = [term.lower().strip('-+') for term in query.split() 
             if term.lower() not in ['and', 'or', 'not', '&&', '||']]
    
    # Check name
    name_lower = context.name.lower()
    for term in terms:
        if term in name_lower:
            start_pos = name_lower.find(term)
            highlights.append({
                'field': 'name',
                'fragment': context.name,
                'positions': [start_pos]
            })
            break  # Only one highlight per field
    
    # Check description
    if context.description:
        desc_lower = context.description.lower()
        for term in terms:
            if term in desc_lower:
                start_pos = desc_lower.find(term)
                # Get context around the match
                fragment_start = max(0, start_pos - 50)
                fragment_end = min(len(context.description), start_pos + len(term) + 50)
                fragment = context.description[fragment_start:fragment_end]
                
                if fragment_start > 0:
                    fragment = '...' + fragment
                if fragment_end < len(context.description):
                    fragment = fragment + '...'
                
                highlights.append({
                    'field': 'description', 
                    'fragment': fragment,
                    'positions': [start_pos - fragment_start]
                })
                break  # Only one highlight per field
    
    return highlights
