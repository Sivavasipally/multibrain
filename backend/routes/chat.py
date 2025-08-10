"""
Chat Routes for RAG Chatbot PWA - Real-time Conversational AI

This module provides comprehensive chat functionality for the RAG (Retrieval-Augmented Generation)
chatbot system. It handles chat session management, message processing, context-aware responses,
and real-time streaming capabilities.

Key Features:
- Chat session lifecycle management (create, retrieve, update, delete)
- RAG-powered conversational AI with context retrieval
- Real-time streaming responses for improved user experience
- Multi-context query support for comprehensive answers
- Message history persistence with metadata
- Context-aware response generation using vector similarity search
- Comprehensive error handling and logging
- JWT-based authentication and authorization

Core Functionality:
1. Session Management: Create and manage chat sessions
2. Message Processing: Handle user queries with context retrieval
3. RAG Integration: Combine retrieved context with LLM generation
4. Streaming Responses: Real-time response streaming
5. Context Switching: Dynamic context selection for queries
6. History Management: Persistent conversation history

API Endpoints:
- GET /sessions: Retrieve user's chat sessions
- POST /sessions: Create new chat session
- GET /sessions/{id}: Get session with message history
- DELETE /sessions/{id}: Delete chat session
- POST /query: Process chat query with RAG
- POST /query/stream: Stream chat response

Dependencies:
- Flask: Web framework and routing
- Flask-JWT-Extended: Authentication and authorization
- SQLAlchemy: Database operations and models
- LLMService: Language model integration (Gemini)
- VectorService: Vector similarity search (FAISS)

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Context, ChatSession, Message
from services.llm_service import LLMService
from services.vector_service import VectorService

# Import logging functionality
from logging_config import get_logger, log_error_with_context
from services.detailed_logger import detailed_logger, track_operation

# Initialize logger
logger = get_logger('chat_routes')

def get_current_user_id():
    """
    Extract and validate user ID from JWT token
    
    This helper function securely extracts the user identity from the JWT token
    in the current request context and converts it to an integer for database operations.
    
    Returns:
        int: The authenticated user's ID if valid token exists
        None: If no token or invalid token
        
    Raises:
        ValueError: If JWT identity cannot be converted to integer
        
    Example:
        >>> user_id = get_current_user_id()
        >>> if user_id:
        ...     user = User.query.get(user_id)
    """
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved user ID {user_id} from JWT token")
            return user_id
        else:
            logger.debug("No user identity found in JWT token")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer: {e}")
        return None

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """
    Retrieve all chat sessions for the authenticated user
    
    Returns a list of chat sessions belonging to the current user,
    ordered by most recently updated first. Each session includes
    metadata such as title, creation time, and last update time.
    
    Authentication:
        Requires valid JWT token in Authorization header
        
    Returns:
        200: Success response with sessions list
        {
            "sessions": [
                {
                    "id": "Session ID",
                    "user_id": "User ID", 
                    "title": "Session title",
                    "created_at": "ISO timestamp",
                    "updated_at": "ISO timestamp"
                }
            ]
        }
        
        401: Unauthorized (invalid or missing JWT token)
        500: Internal server error
        
    Example:
        GET /api/chat/sessions
        Authorization: Bearer <jwt_token>
        
    Note:
        Sessions are automatically ordered by updated_at descending
        to show most recent conversations first.
    """
    client_ip = request.remote_addr
    logger.info(f"Chat sessions request from user, IP: {client_ip}")
    
    try:
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized chat sessions request from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.debug(f"Fetching chat sessions for user {user_id}")
        
        # Query sessions ordered by most recent first
        sessions = ChatSession.query.filter_by(user_id=user_id)\
                                   .order_by(ChatSession.updated_at.desc())\
                                   .all()
        
        session_count = len(sessions)
        logger.info(f"Retrieved {session_count} chat sessions for user {user_id}")
        
        # Convert to dictionary format
        sessions_data = [session.to_dict() for session in sessions]
        
        return jsonify({
            'sessions': sessions_data,
            'count': session_count
        }), 200
        
    except Exception as e:
        error_msg = f"Error fetching chat sessions: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "endpoint": "get_chat_sessions",
            "user_id": user_id if 'user_id' in locals() else None,
            "client_ip": client_ip
        })
        return jsonify({'error': 'Failed to retrieve chat sessions'}), 500

@chat_bp.route('/sessions', methods=['OPTIONS'])
def create_chat_session_options():
    """Handle CORS preflight requests for chat session creation"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@chat_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    """Create a new chat session"""
    try:
        user_id = get_current_user_id()
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
        user_id = get_current_user_id()
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
        user_id = get_current_user_id()
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not session:
            return jsonify({'error': 'Chat session not found'}), 404
        
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'message': 'Chat session deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/query', methods=['OPTIONS'])
def chat_query_options():
    """Handle CORS preflight requests for chat query"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@chat_bp.route('/query', methods=['POST'])
@jwt_required()
def chat_query():
    """
    Process a chat query using RAG (Retrieval-Augmented Generation)
    
    This is the core endpoint of the RAG chatbot system. It processes user queries
    by retrieving relevant context from selected knowledge bases and generating
    AI-powered responses using the retrieved information.
    
    RAG Process:
    1. Query Validation: Validate user input and session
    2. Context Retrieval: Search vector stores for relevant chunks
    3. Context Ranking: Rank retrieved chunks by similarity score
    4. Prompt Construction: Build enhanced prompt with retrieved context
    5. LLM Generation: Generate response using context-aware prompt
    6. Response Processing: Format response with citations and metadata
    7. Message Persistence: Save conversation to database
    
    Request Body:
        {
            "message": "string (required) - User's chat message/question",
            "session_id": "integer (required) - Chat session ID",
            "context_ids": "array (optional) - List of context IDs to search",
            "stream": "boolean (optional) - Enable streaming response (default: false)",
            "max_results": "integer (optional) - Maximum retrieved chunks (default: 5)",
            "similarity_threshold": "float (optional) - Minimum similarity score (default: 0.1)"
        }
        
    Returns:
        200: Successful response (non-streaming)
        {
            "response": "AI-generated response text",
            "sources": [
                {
                    "content": "Retrieved text chunk",
                    "source": "Source document name", 
                    "score": "Similarity score",
                    "chunk_index": "Chunk position"
                }
            ],
            "metadata": {
                "tokens_used": "Token count",
                "model_used": "LLM model name",
                "contexts_searched": "Number of contexts",
                "processing_time": "Response time in ms"
            }
        }
        
        Stream Response: text/plain with real-time chunks (if stream=true)
        400: Bad request (missing fields, invalid data)
        401: Unauthorized (invalid JWT)
        404: Session not found
        500: Internal server error
        
    Authentication:
        Requires valid JWT token with user access to session and contexts
        
    Example:
        POST /api/chat/query
        Authorization: Bearer <jwt_token>
        {
            "message": "What are the main features?",
            "session_id": 1,
            "context_ids": [1, 2],
            "stream": false
        }
    """
    client_ip = request.remote_addr
    start_time = logger.info(f"RAG query request from {client_ip}")
    
    try:
        # Authenticate user
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized RAG query attempt from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Parse and validate request data
        data = request.get_json()
        if not data:
            logger.warning(f"RAG query with no JSON data from user {user_id}")
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate required fields
        required_fields = ('message', 'session_id')
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"RAG query missing fields {missing_fields} from user {user_id}")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        message = data['message'].strip()
        session_id = data['session_id']
        context_ids = data.get('context_ids', [])
        stream = data.get('stream', False)
        max_results = data.get('max_results', 5)
        
        # Log comprehensive query details and user activity
        logger.info(f"Processing RAG query from user {user_id}: session={session_id}, contexts={len(context_ids)}, stream={stream}")
        logger.debug(f"Query preview: '{message[:100]}{'...' if len(message) > 100 else ''}'")
        
        # Log user activity
        detailed_logger.log_user_activity(
            user_id=user_id,
            session_id=session_id,
            activity_type="chat_query",
            details={
                'message_length': len(message),
                'context_ids': context_ids,
                'streaming': stream,
                'client_ip': client_ip,
                'query_preview': message[:50] + ('...' if len(message) > 50 else '')
            }
        )
        
        # Validate and retrieve session
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not session:
            logger.warning(f"Session {session_id} not found for user {user_id}")
            return jsonify({'error': 'Chat session not found or access denied'}), 404
        
        # Validate and retrieve contexts
        if context_ids:
            contexts = Context.query.filter(
                Context.id.in_(context_ids),
                Context.user_id == user_id,
                Context.status == 'ready'
            ).all()
            
            found_context_ids = [ctx.id for ctx in contexts]
            missing_contexts = set(context_ids) - set(found_context_ids)
            if missing_contexts:
                logger.warning(f"Contexts {missing_contexts} not found or not ready for user {user_id}")
        else:
            # If no contexts specified, use all user's ready contexts
            contexts = Context.query.filter_by(user_id=user_id, status='ready').all()
            logger.debug(f"No contexts specified, using all {len(contexts)} ready contexts for user {user_id}")
        
        if not contexts:
            logger.error(f"No valid contexts available for user {user_id}")
            return jsonify({'error': 'No valid contexts selected or available'}), 400
        
        context_names = [ctx.name for ctx in contexts]
        logger.info(f"Using contexts for RAG: {context_names}")
        
        # Save user message to database
        try:
            user_message = Message(
                session_id=session.id,
                role='user',
                content=message
            )
            user_message.set_context_ids(context_ids)
            
            db.session.add(user_message)
            db.session.commit()
            
            logger.debug(f"Saved user message to database: message_id={user_message.id}")
            
        except Exception as db_error:
            logger.error(f"Failed to save user message: {db_error}")
            db.session.rollback()
            # Continue processing - don't fail the query for database issues
        
        # Process query based on streaming preference
        if stream:
            logger.info(f"Starting streaming RAG response for user {user_id}")
            return Response(
                stream_with_context(generate_streaming_response(
                    message, contexts, session, user_message.id if 'user_message' in locals() else None
                )),
                mimetype='text/plain',
                headers={'Cache-Control': 'no-cache'}
            )
        else:
            logger.info(f"Starting non-streaming RAG response for user {user_id}")
            response_data = generate_response(message, contexts, session, user_message.id if 'user_message' in locals() else None)
            
            # Log response summary
            if response_data:
                response_length = len(response_data.get('response', ''))
                sources_count = len(response_data.get('sources', []))
                logger.info(f"Generated RAG response: {response_length} chars, {sources_count} sources")
            
            return jsonify(response_data), 200
        
    except ValueError as e:
        error_msg = f"Invalid request data: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        error_msg = f"RAG query processing failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "endpoint": "chat_query",
            "user_id": user_id if 'user_id' in locals() else None,
            "session_id": session_id if 'session_id' in locals() else None,
            "context_ids": context_ids if 'context_ids' in locals() else None,
            "client_ip": client_ip,
            "message_length": len(message) if 'message' in locals() else 0
        })
        
        # Rollback any database changes
        try:
            db.session.rollback()
        except:
            pass
            
        return jsonify({'error': 'Failed to process chat query'}), 500

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

            # Skip contexts that don't have vector stores yet
            if not context.vector_store_path:
                print(f"Skipping context {context.name} - no vector store found (no documents uploaded yet)")
                continue
                
            # Check if vector store actually exists
            import os
            if not os.path.exists(context.vector_store_path):
                print(f"Skipping context {context.name} - vector store path does not exist: {context.vector_store_path}")
                continue

            chunks = vector_service.search_similar(
                context.vector_store_path, 
                query, 
                top_k=5,
                context_id=context.id
            )
            logger.info(f"Found {len(chunks)} chunks from context {context.name} (ID: {context.id})")

            for chunk in chunks:
                all_chunks.append(chunk)
                citations.append({
                    'context_id': context.id,
                    'context_name': context.name,
                    'source': chunk.get('source', ''),
                    'score': chunk.get('score', 0.0)
                })
        
        # Check if we found any chunks from any context
        if not all_chunks:
            print(f"Warning: No chunks found from any of the {len(contexts)} selected contexts")
            print("This might be because:")
            print("1. No documents have been uploaded to these contexts yet")
            print("2. The vector stores haven't been created yet")
            print("3. The query doesn't match any content in the uploaded documents")
            
            # Create a response indicating no relevant context was found
            no_context_response = f"""I don't have any information to answer your question about "{query}" because:

• The selected context(s) don't contain any documents yet, or
• No relevant information was found in the available documents

To get better answers:
1. Upload documents to your selected contexts
2. Make sure the documents contain information relevant to your question
3. Try rephrasing your question

Selected contexts: {', '.join(context.name for context in contexts)}
"""
            
            # Save a response indicating no context was available
            assistant_message = Message(
                session_id=session.id,
                role='assistant',
                content=no_context_response,
                tokens_used=0,
                model_used='system-message'
            )
            assistant_message.set_context_ids([c.id for c in contexts])
            assistant_message.set_citations([])
            
            db.session.add(assistant_message)
            db.session.commit()
            
            return {
                'message': assistant_message.to_dict(),
                'citations': []
            }
        
        # Generate response using LLM with enhanced logging
        response = llm_service.generate_response(
            query=query,
            context_chunks=all_chunks,
            chat_history=get_recent_messages(session.id),
            user_id=session.user_id,
            session_id=session.id,
            contexts_searched=[ctx.id for ctx in contexts]
        )
        
        # Save assistant message
        assistant_message = Message(
            session_id=session.id,
            role='assistant',
            content=response['content'],
            tokens_used=response.get('tokens_used', 0),
            model_used=response.get('model_used', 'gemini-2.0-flash')
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
            
            # Skip contexts that don't have vector stores yet
            if not context.vector_store_path:
                print(f"Streaming - Skipping context {context.name} - no vector store found (no documents uploaded yet)")
                continue
                
            # Check if vector store actually exists
            import os
            if not os.path.exists(context.vector_store_path):
                print(f"Streaming - Skipping context {context.name} - vector store path does not exist: {context.vector_store_path}")
                continue
                
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
        
        # Check if we found any chunks from any context
        if not all_chunks:
            print(f"Streaming - Warning: No chunks found from any of the {len(contexts)} selected contexts")
            
            # Create a response indicating no relevant context was found
            no_context_response = f"""I don't have any information to answer your question about "{query}" because:

• The selected context(s) don't contain any documents yet, or
• No relevant information was found in the available documents

To get better answers:
1. Upload documents to your selected contexts
2. Make sure the documents contain information relevant to your question
3. Try rephrasing your question

Selected contexts: {', '.join(context.name for context in contexts)}
"""
            
            # Stream the no-context response
            for char in no_context_response:
                yield f"data: {json.dumps({'chunk': char})}\n\n"
            
            # Save the complete response
            assistant_message = Message(
                session_id=session.id,
                role='assistant',
                content=no_context_response,
                model_used='system-message'
            )
            assistant_message.set_context_ids([c.id for c in contexts])
            assistant_message.set_citations([])
            
            db.session.add(assistant_message)
            db.session.commit()
            
            # Send final message with empty citations
            yield f"data: {json.dumps({'done': True, 'citations': []})}\n\n"
            return
        
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
            model_used='gemini-2.0-flash'
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
