"""
Chat routes for RAG Chatbot PWA
"""

import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Context, ChatSession, Message
from services.llm_service import LLMService
from services.vector_service import VectorService

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """Get all chat sessions for the current user"""
    try:
        user_id = get_jwt_identity()
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    """Create a new chat session"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        session = ChatSession(
            user_id=user_id,
            title=data.get('title', 'New Chat')
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Chat session created successfully',
            'session': session.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_chat_session(session_id):
    """Get a specific chat session with messages"""
    try:
        user_id = get_jwt_identity()
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not session:
            return jsonify({'error': 'Chat session not found'}), 404
        
        # Get messages
        messages = [message.to_dict() for message in session.messages]
        session_dict = session.to_dict()
        session_dict['messages'] = messages
        
        return jsonify({'session': session_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    """Delete a chat session"""
    try:
        user_id = get_jwt_identity()
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not session:
            return jsonify({'error': 'Chat session not found'}), 404
        
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'message': 'Chat session deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/query', methods=['POST'])
@jwt_required()
def chat_query():
    """Process a chat query with RAG"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ('message', 'session_id')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get session
        session = ChatSession.query.filter_by(id=data['session_id'], user_id=user_id).first()
        if not session:
            return jsonify({'error': 'Chat session not found'}), 404
        
        # Get selected contexts
        context_ids = data.get('context_ids', [])
        contexts = Context.query.filter(
            Context.id.in_(context_ids),
            Context.user_id == user_id,
            Context.status == 'ready'
        ).all()
        
        if not contexts:
            return jsonify({'error': 'No valid contexts selected'}), 400
        
        # Save user message
        user_message = Message(
            session_id=session.id,
            role='user',
            content=data['message']
        )
        user_message.set_context_ids(context_ids)
        
        db.session.add(user_message)
        db.session.commit()
        
        # Check if streaming is requested
        stream = data.get('stream', False)
        
        if stream:
            return Response(
                stream_with_context(generate_streaming_response(
                    data['message'], contexts, session, user_message.id
                )),
                mimetype='text/plain'
            )
        else:
            # Non-streaming response
            response_data = generate_response(data['message'], contexts, session, user_message.id)
            return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def generate_response(query, contexts, session, user_message_id):
    """Generate a non-streaming response"""
    try:
        # Initialize services
        # Use the embedding model from the first context (they should all be the same)
        embedding_model = contexts[0].embedding_model if contexts else 'text-embedding-004'
        vector_service = VectorService(embedding_model)
        llm_service = LLMService()

        # Retrieve relevant chunks from contexts
        all_chunks = []
        citations = []

        print(f"Processing query: {query}")
        print(f"Using {len(contexts)} contexts")

        for context in contexts:
            print(f"Searching context: {context.name} (ID: {context.id})")
            print(f"Context embedding model: {context.embedding_model}")
            print(f"Vector store path: {context.vector_store_path}")

            chunks = vector_service.search_similar(context.vector_store_path, query, top_k=5)
            print(f"Found {len(chunks)} chunks from context {context.name}")

            for chunk in chunks:
                all_chunks.append(chunk)
                citations.append({
                    'context_id': context.id,
                    'context_name': context.name,
                    'source': chunk.get('source', ''),
                    'score': chunk.get('score', 0.0)
                })
        
        # Generate response using LLM
        response = llm_service.generate_response(
            query=query,
            context_chunks=all_chunks,
            chat_history=get_recent_messages(session.id)
        )
        
        # Save assistant message
        assistant_message = Message(
            session_id=session.id,
            role='assistant',
            content=response['content'],
            tokens_used=response.get('tokens_used', 0),
            model_used=response.get('model_used', 'gemini-pro')
        )
        assistant_message.set_context_ids([c.id for c in contexts])
        assistant_message.set_citations(citations)
        
        db.session.add(assistant_message)
        
        # Update session title if it's the first message
        if session.title == 'New Chat' and len(session.messages) <= 2:
            session.title = query[:50] + ('...' if len(query) > 50 else '')
        
        db.session.commit()
        
        return {
            'message': assistant_message.to_dict(),
            'citations': citations
        }
        
    except Exception as e:
        db.session.rollback()
        raise e

def generate_streaming_response(query, contexts, session, user_message_id):
    """Generate a streaming response"""
    try:
        # Initialize services
        # Use the embedding model from the first context (they should all be the same)
        embedding_model = contexts[0].embedding_model if contexts else 'text-embedding-004'
        vector_service = VectorService(embedding_model)
        llm_service = LLMService()

        # Retrieve relevant chunks
        all_chunks = []
        citations = []

        print(f"Streaming - Processing query: {query}")
        print(f"Streaming - Using {len(contexts)} contexts")

        for context in contexts:
            print(f"Streaming - Searching context: {context.name} (ID: {context.id})")
            chunks = vector_service.search_similar(context.vector_store_path, query, top_k=5)
            print(f"Streaming - Found {len(chunks)} chunks from context {context.name}")

            for chunk in chunks:
                all_chunks.append(chunk)
                citations.append({
                    'context_id': context.id,
                    'context_name': context.name,
                    'source': chunk.get('source', ''),
                    'score': chunk.get('score', 0.0)
                })
        
        # Stream response
        full_response = ""
        for chunk in llm_service.generate_streaming_response(
            query=query,
            context_chunks=all_chunks,
            chat_history=get_recent_messages(session.id)
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save complete response
        assistant_message = Message(
            session_id=session.id,
            role='assistant',
            content=full_response,
            model_used='gemini-pro'
        )
        assistant_message.set_context_ids([c.id for c in contexts])
        assistant_message.set_citations(citations)
        
        db.session.add(assistant_message)
        
        # Update session title if needed
        if session.title == 'New Chat' and len(session.messages) <= 2:
            session.title = query[:50] + ('...' if len(query) > 50 else '')
        
        db.session.commit()
        
        # Send final message with citations
        yield f"data: {json.dumps({'done': True, 'citations': citations})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

def get_recent_messages(session_id, limit=10):
    """Get recent messages for context"""
    messages = Message.query.filter_by(session_id=session_id)\
                          .order_by(Message.created_at.desc())\
                          .limit(limit).all()
    
    return [{'role': msg.role, 'content': msg.content} for msg in reversed(messages)]
