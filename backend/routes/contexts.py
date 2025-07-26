"""
Context management routes for RAG Chatbot PWA
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Context, Document
# Note: Celery tasks not available in local version
# # from tasks.context_processor import process_context_task  # Disabled for local version

contexts_bp = Blueprint('contexts', __name__)

@contexts_bp.route('/', methods=['GET'])
@jwt_required()
def get_contexts():
    """Get all contexts for the current user"""
    try:
        user_id = get_jwt_identity()
        contexts = Context.query.filter_by(user_id=user_id).order_by(Context.created_at.desc()).all()
        
        return jsonify({
            'contexts': [context.to_dict() for context in contexts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/', methods=['POST'])
@jwt_required()
def create_context():
    """Create a new context"""
    try:
        user_id = get_jwt_identity()
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
        user_id = get_jwt_identity()
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
        user_id = get_jwt_identity()
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
        user_id = get_jwt_identity()

        # Use comprehensive cleanup service
        from services.context_cleanup_service import ContextCleanupService
        cleanup_service = ContextCleanupService()

        result = cleanup_service.delete_context_completely(context_id, user_id)

        if result['success']:
            return jsonify({
                'message': result['message'],
                'cleanup_stats': result['stats']
            }), 200
        else:
            return jsonify({
                'error': result['error'],
                'cleanup_stats': result['stats']
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_context(context_id):
    """Reprocess a context"""
    try:
        user_id = get_jwt_identity()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        # Reset status and start reprocessing
        context.status = 'pending'
        context.progress = 0
        context.error_message = None
        
        db.session.commit()
        
        # Start background processing
        # # process_context_task.delay(context.id)
        
        return jsonify({
            'message': 'Context reprocessing started',
            'context': context.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contexts_bp.route('/<int:context_id>/status', methods=['GET'])
@jwt_required()
def get_context_status(context_id):
    """Get context processing status"""
    try:
        user_id = get_jwt_identity()
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
