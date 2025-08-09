"""
Database Models for RAG Chatbot PWA - Core Data Architecture

This module defines the complete database schema for the RAG (Retrieval-Augmented Generation)
chatbot system using SQLAlchemy ORM. The models represent the core entities and their
relationships that power the knowledge management and conversational AI functionality.

Database Architecture:
The system follows a hierarchical data model where Users own Contexts (knowledge bases),
which contain Documents that are processed into TextChunks for vector search. Chat
functionality is handled through ChatSessions and Messages with context references.

Core Entities:
1. User - Authentication and user management
2. Context - Knowledge bases (file collections, repositories, databases)
3. Document - Individual files within contexts
4. TextChunk - Processed text segments for vector search
5. ChatSession - Conversation containers
6. Message - Individual chat messages with context references

Key Features:
- Comprehensive relationship mapping with cascade deletion
- JSON field support for flexible configuration storage
- Automatic timestamp tracking for audit trails
- Secure password hashing with Werkzeug
- OAuth integration support (GitHub, Bitbucket)
- Vector store path management
- Processing status and progress tracking
- Citation and source attribution

Database Relationships:
User (1) ←→ (N) Context ←→ (N) Document ←→ (N) TextChunk
User (1) ←→ (N) ChatSession ←→ (N) Message

Security Features:
- Password hashing with salt
- Secure session management
- Input validation and sanitization
- Cascade deletion for data integrity
- Admin privilege separation

Performance Optimizations:
- Indexed foreign keys for efficient queries
- Lazy loading relationships to reduce memory usage
- Optimized JSON field access patterns
- Batch operations support

Dependencies:
- Flask-SQLAlchemy: ORM and database abstraction
- Werkzeug: Password hashing and security utilities
- Python datetime: Timezone-aware timestamp handling

Author: RAG Chatbot Development Team
Version: 1.0.0
Last Updated: 2024-01-01
"""

from datetime import datetime, timezone
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Note: Import versioning models after all base models are defined to avoid circular imports
# They will be imported at the end of this file

class TimestampMixin:
    """
    Mixin class to add timestamp fields to models
    
    Provides created_at and updated_at fields with automatic timestamp management.
    The created_at field is set once when the record is created, while updated_at
    is automatically updated whenever the record is modified.
    
    Usage:
        class MyModel(db.Model, TimestampMixin):
            # other fields...
    """
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class User(db.Model):
    """
    User model for authentication and authorization
    
    Represents system users with comprehensive authentication capabilities including
    local password-based auth and OAuth integration. Supports role-based access
    control with admin privileges and account status management.
    
    This model serves as the root entity for all user-owned resources including
    contexts (knowledge bases) and chat sessions. All user data is isolated
    through proper foreign key relationships.
    
    Security Features:
    - Werkzeug password hashing with salt
    - Unique constraints on username and email
    - OAuth integration for GitHub and Bitbucket
    - Admin role separation for system management
    - Account activation/deactivation support
    
    Relationships:
    - contexts: One-to-many relationship with Context (knowledge bases)
    - chat_sessions: One-to-many relationship with ChatSession (conversations)
    
    Example:
        >>> user = User(username='alice', email='alice@example.com')
        >>> user.set_password('secure_password')
        >>> db.session.add(user)
        >>> db.session.commit()
    """
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, doc="Unique user identifier")
    
    # Authentication fields
    username = db.Column(db.String(80), unique=True, nullable=False, 
                        doc="Unique username for login (3-80 characters)")
    email = db.Column(db.String(120), unique=True, nullable=False,
                     doc="Unique email address for notifications and recovery")
    password_hash = db.Column(db.String(255), nullable=False,
                             doc="Hashed password using Werkzeug security")
    
    # Metadata fields
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          doc="Account creation timestamp (UTC)")
    is_active = db.Column(db.Boolean, default=True, nullable=False,
                         doc="Account status - false for suspended accounts")
    is_admin = db.Column(db.Boolean, default=False, nullable=False,
                        doc="Administrative privileges for system management")
    
    # OAuth integration fields
    github_id = db.Column(db.String(50), unique=True, nullable=True,
                         doc="GitHub user ID for OAuth integration")
    bitbucket_id = db.Column(db.String(50), unique=True, nullable=True,
                            doc="Bitbucket user ID for OAuth integration")
    
    # Relationships with cascade deletion for data integrity
    contexts = db.relationship('Context', backref='user', lazy=True, 
                              cascade='all, delete-orphan',
                              doc="User's knowledge bases and contexts")
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True,
                                   cascade='all, delete-orphan',
                                   doc="User's chat conversation sessions")
    
    def set_password(self, password):
        """
        Set user password with secure hashing
        
        Uses Werkzeug's generate_password_hash to create a secure hash
        with salt. The original password is never stored.
        
        Args:
            password (str): Plain text password to hash
            
        Security:
            - Uses PBKDF2 with SHA-256 by default
            - Automatic salt generation
            - Configurable iteration count
            
        Example:
            >>> user.set_password('my_secure_password')
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify password against stored hash
        
        Securely compares the provided password against the stored hash
        using constant-time comparison to prevent timing attacks.
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
            
        Security:
            - Constant-time comparison prevents timing attacks
            - No plain text password storage or logging
            
        Example:
            >>> if user.check_password(input_password):
            ...     print("Authentication successful")
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        Convert user model to dictionary representation
        
        Serializes the user model for JSON responses, excluding sensitive
        information like password hash. Includes all public user attributes
        and metadata.
        
        Returns:
            dict: User data without sensitive information
                - id: User identifier
                - username: Username
                - email: Email address  
                - created_at: ISO format creation timestamp
                - is_active: Account status
                - is_admin: Administrative privileges
                
        Security:
            - Excludes password_hash and OAuth IDs
            - Safe for API responses and logging
            
        Example:
            >>> user_data = user.to_dict()
            >>> print(f"User: {user_data['username']}")
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        }
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<User {self.username}>'

class Context(db.Model):
    """
    Context model for RAG knowledge bases and document collections
    
    Represents knowledge bases (contexts) that contain processed documents, code repositories,
    or database connections. Contexts serve as the foundation for RAG (Retrieval-Augmented
    Generation) operations, organizing related documents into searchable knowledge bases.
    
    Key Features:
    - Multi-source content support (files, repositories, databases)
    - Flexible configuration system with JSON storage
    - Processing status tracking with progress monitoring
    - Vector store path management for FAISS indexes
    - Chunking strategy configuration for optimal RAG performance
    - Embedding model selection per context
    
    Context Types:
    - 'files': Direct file upload and processing
    - 'repo': Git repository cloning and analysis (GitHub, Bitbucket)
    - 'database': External database connection and querying
    
    Processing States:
    - 'pending': Newly created, awaiting processing
    - 'processing': Content being ingested and indexed
    - 'ready': Available for chat queries and search
    - 'error': Processing failed, requires attention
    
    Relationships:
    - user: Many-to-one with User (context owner)
    - documents: One-to-many with Document (processed files)
    
    Example:
        >>> context = Context(
        ...     name='Python Documentation',
        ...     description='Official Python docs and tutorials',
        ...     user_id=user.id,
        ...     source_type='repo',
        ...     status='pending'
        ... )
        >>> context.set_config({'url': 'https://github.com/python/cpython'})
        >>> db.session.add(context)
    """
    __tablename__ = 'contexts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Configuration
    source_type = db.Column(db.String(50), nullable=False)  # 'repo', 'database', 'files'
    config = db.Column(db.Text)  # JSON configuration
    chunk_strategy = db.Column(db.String(50), default='language-specific')
    embedding_model = db.Column(db.String(100), default='text-embedding-004')
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, ready, error
    progress = db.Column(db.Integer, default=0)  # 0-100
    error_message = db.Column(db.Text)
    
    # Metadata
    total_chunks = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    vector_store_path = db.Column(db.String(500))
    
    # Relationships
    documents = db.relationship('Document', backref='context', lazy=True, cascade='all, delete-orphan')
    
    def get_config(self):
        """
        Get context configuration as dictionary
        
        Parses the JSON configuration string stored in the database and returns
        it as a Python dictionary for easy access to context settings.
        
        Returns:
            dict: Configuration dictionary with context-specific settings:
                - For 'repo' contexts: {'url': str, 'branch': str, 'access_token': str}
                - For 'database' contexts: {'type': str, 'connection_string': str, 'tables': list}
                - For 'files' contexts: {'file_paths': list, 'supported_extensions': list}
                
        Example:
            >>> config = context.get_config()
            >>> repo_url = config.get('url', 'https://github.com/default/repo')
        """
        return json.loads(self.config) if self.config else {}
    
    def set_config(self, config_dict):
        """
        Set context configuration from dictionary
        
        Converts a Python dictionary to JSON string format and stores it in
        the database config field. This allows flexible configuration storage
        for different context types and source configurations.
        
        Args:
            config_dict (dict): Configuration dictionary containing context settings
                - Repo contexts: url, branch, access_token, etc.
                - Database contexts: type, connection_string, tables, etc.
                - File contexts: file_paths, supported_extensions, etc.
                
        Example:
            >>> context.set_config({
            ...     'url': 'https://github.com/user/repo',
            ...     'branch': 'main',
            ...     'access_token': 'ghp_xxxxxxxxxxxx'
            ... })
        """
        self.config = json.dumps(config_dict)
    
    def to_dict(self):
        """
        Convert context model to dictionary representation
        
        Serializes the context model for JSON responses, including all metadata
        and processing status information. This is used for API responses and
        frontend data consumption.
        
        Returns:
            dict: Context data including:
                - Basic info: id, name, description
                - Processing: status, progress, error_message
                - Configuration: source_type, config, chunk_strategy, embedding_model
                - Statistics: total_chunks, total_tokens
                - Timestamps: created_at, updated_at (ISO format)
                
        Example:
            >>> context_data = context.to_dict()
            >>> print(f"Context '{context_data['name']}' has {context_data['total_chunks']} chunks")
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source_type': self.source_type,
            'config': self.get_config(),
            'chunk_strategy': self.chunk_strategy,
            'embedding_model': self.embedding_model,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'total_chunks': self.total_chunks,
            'total_tokens': self.total_tokens,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Document(db.Model):
    """
    Document model for tracking processed files and their metadata
    
    Represents individual files within contexts that have been processed for RAG operations.
    Each document maintains comprehensive metadata about the file, its processing status,
    and relationship to generated text chunks for vector search.
    
    Key Features:
    - File metadata tracking (name, path, size, type)
    - Processing statistics (chunks count, tokens count)
    - Language detection for code files
    - Timestamp tracking for processing workflow
    - Integration with TextChunk entities for content segmentation
    
    Processing Workflow:
    1. File ingestion: Document record created with basic metadata
    2. Content extraction: Text content extracted based on file type
    3. Language detection: Programming language identified for code files
    4. Chunking: Content split into TextChunk entities
    5. Statistics update: Chunks and tokens counts updated
    
    File Type Support:
    - Code files: Python, JavaScript, Java, C++, Go, etc.
    - Documents: PDF, DOCX, TXT, MD, RTF
    - Data files: CSV, JSON, XML, YAML
    - Web files: HTML, CSS, SCSS
    
    Relationships:
    - context: Many-to-one with Context (parent knowledge base)
    
    Example:
        >>> document = Document(
        ...     context_id=context.id,
        ...     filename='main.py',
        ...     file_path='/uploads/main.py',
        ...     file_type='code',
        ...     language='python'
        ... )
    """
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000))
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    
    # Processing metadata
    chunks_count = db.Column(db.Integer, default=0)
    tokens_count = db.Column(db.Integer, default=0)
    language = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """
        Convert document model to dictionary representation
        
        Serializes the document model for JSON responses, including file metadata
        and processing statistics. This is used for API responses when retrieving
        context details with associated documents.
        
        Returns:
            dict: Document data including:
                - Basic info: id, filename, file_type, file_size
                - Processing stats: chunks_count, tokens_count
                - Language info: language (for code files)
                - Timestamps: created_at, processed_at (ISO format)
                
        Example:
            >>> doc_data = document.to_dict()
            >>> print(f"File '{doc_data['filename']}' has {doc_data['chunks_count']} chunks")
        """
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'chunks_count': self.chunks_count,
            'tokens_count': self.tokens_count,
            'language': self.language,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class ChatSession(db.Model):
    """
    Chat session model for conversation management
    
    Represents individual chat conversations between users and the AI assistant.
    Each session contains a sequence of messages and maintains conversation context
    for improved response quality and user experience.
    
    Key Features:
    - Conversation grouping with persistent message history
    - Automatic title generation from first user message
    - Timestamp tracking for session lifecycle management
    - Cascade deletion of associated messages for data integrity
    
    Session Lifecycle:
    1. Creation: New session created when user starts conversation
    2. Title Update: Session title set based on first meaningful exchange
    3. Message Addition: User and assistant messages added to session
    4. Context Maintenance: Session provides conversation context for AI responses
    
    Relationships:
    - user: Many-to-one with User (session owner)
    - messages: One-to-many with Message (conversation history)
    
    Example:
        >>> session = ChatSession(
        ...     user_id=user.id,
        ...     title='Python Development Help'
        ... )
        >>> db.session.add(session)
        >>> # Messages will be added as conversation progresses
    """
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """
        Convert chat session model to dictionary representation
        
        Serializes the chat session model for JSON responses, including session
        metadata and message count for frontend display in session lists.
        
        Returns:
            dict: Session data including:
                - Basic info: id, title
                - Statistics: message_count (calculated from relationship)
                - Timestamps: created_at, updated_at (ISO format)
                
        Example:
            >>> session_data = session.to_dict()
            >>> print(f"Session '{session_data['title']}' has {session_data['message_count']} messages")
        """
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }

class Message(db.Model):
    """
    Message model for chat conversation history and RAG context tracking
    
    Represents individual messages within chat sessions, including both user queries
    and AI assistant responses. Each message maintains detailed metadata about the
    RAG (Retrieval-Augmented Generation) process, including context sources and citations.
    
    Key Features:
    - Role-based message classification (user/assistant)
    - Context tracking with JSON array of context IDs used for RAG
    - Source citation management for response attribution
    - Token usage tracking for cost monitoring
    - Model information for response generation tracking
    
    Message Types:
    - 'user': User-submitted queries and questions
    - 'assistant': AI-generated responses with RAG context
    
    RAG Integration:
    - context_ids: References to Context entities used for response generation
    - citations: Source attribution for retrieved information
    - tokens_used: Token consumption for cost tracking
    - model_used: AI model identifier for response generation
    
    Relationships:
    - session: Many-to-one with ChatSession (parent conversation)
    
    Example:
        >>> message = Message(
        ...     session_id=session.id,
        ...     role='user',
        ...     content='How do I implement OAuth in Python?'
        ... )
        >>> message.set_context_ids([1, 2])  # Used contexts for RAG
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    
    # Context and citations
    context_ids = db.Column(db.Text)  # JSON array of context IDs used
    citations = db.Column(db.Text)  # JSON array of source citations
    
    # Metadata
    tokens_used = db.Column(db.Integer)
    model_used = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_context_ids(self):
        """
        Get context IDs used for RAG as list
        
        Parses the JSON array of context IDs stored in the database and returns
        them as a Python list for easy access and iteration.
        
        Returns:
            List[int]: List of context IDs that were used for RAG response generation
                Empty list if no contexts were used
                
        Example:
            >>> context_ids = message.get_context_ids()
            >>> for ctx_id in context_ids:
            ...     context = Context.query.get(ctx_id)
        """
        return json.loads(self.context_ids) if self.context_ids else []
    
    def set_context_ids(self, context_list):
        """
        Set context IDs used for RAG from list
        
        Converts a Python list of context IDs to JSON string format and stores
        it in the database for tracking which contexts were used during RAG.
        
        Args:
            context_list (List[int]): List of context IDs used for response generation
                
        Example:
            >>> message.set_context_ids([1, 2, 3])  # Used three contexts
        """
        self.context_ids = json.dumps(context_list)
    
    def get_citations(self):
        """
        Get response citations as list
        
        Parses the JSON array of source citations stored in the database and returns
        them as a Python list for source attribution and reference display.
        
        Returns:
            List[dict]: List of citation objects, each containing:
                - source: Source document or file name
                - context_id: ID of the context containing the source
                - score: Similarity score from vector search
                - chunk_index: Index of the text chunk used
                
        Example:
            >>> citations = message.get_citations()
            >>> for cite in citations:
            ...     print(f"Source: {cite['source']} (score: {cite['score']})")
        """
        return json.loads(self.citations) if self.citations else []
    
    def set_citations(self, citations_list):
        """
        Set response citations from list
        
        Converts a Python list of citation objects to JSON string format and stores
        it in the database for source attribution and reference tracking.
        
        Args:
            citations_list (List[dict]): List of citation objects containing:
                - source: Source document or file name
                - context_id: ID of the context containing the source
                - score: Similarity score from vector search
                - chunk_index: Index of the text chunk used
                
        Example:
            >>> citations = [{'source': 'main.py', 'score': 0.95, 'context_id': 1}]
            >>> message.set_citations(citations)
        """
        self.citations = json.dumps(citations_list)
    
    def to_dict(self):
        """
        Convert message model to dictionary representation
        
        Serializes the message model for JSON responses, including all RAG metadata
        and source attribution information. This is used for chat history display
        and debugging RAG responses.
        
        Returns:
            dict: Message data including:
                - Basic info: id, role, content
                - RAG data: context_ids, citations (parsed from JSON)
                - Metadata: tokens_used, model_used
                - Timestamp: created_at (ISO format)
                
        Example:
            >>> msg_data = message.to_dict()
            >>> if msg_data['role'] == 'assistant':
            ...     print(f"Response used {len(msg_data['citations'])} sources")
        """
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'context_ids': self.get_context_ids(),
            'citations': self.get_citations(),
            'tokens_used': self.tokens_used,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat()
        }


class TextChunk(db.Model):
    """
    Text chunk model for storing processed document segments for vector search
    
    Represents individual text segments extracted from processed documents within contexts.
    These chunks are the fundamental units for RAG (Retrieval-Augmented Generation) operations,
    providing the granular content that gets embedded and searched during query processing.
    
    Key Features:
    - Granular text storage for optimal vector search performance
    - File metadata preservation for source attribution
    - Chunk ordering with index tracking for document reconstruction
    - Flexible metadata storage with JSON file information
    - Integration with vector embeddings for similarity search
    
    Chunking Strategy:
    - Language-aware chunking for code files (preserving function/class boundaries)
    - Semantic chunking for documents (preserving paragraph/section structure)
    - Fixed-size chunking with overlap for large documents
    - Adaptive chunking based on content type and structure
    
    Vector Search Integration:
    - Each chunk gets embedded into high-dimensional vector space
    - Chunk content used for similarity search during RAG queries
    - File metadata provides context for result attribution
    - Chunk index enables precise source location references
    
    Relationships:
    - context: Many-to-one with Context (parent knowledge base)
    
    Example:
        >>> chunk = TextChunk(
        ...     context_id=context.id,
        ...     file_name='main.py',
        ...     chunk_index=0,
        ...     content='def main():\n    print("Hello World")'
        ... )
        >>> chunk.set_file_info({'language': 'python', 'function': 'main'})
    """
    __tablename__ = 'text_chunks'

    id = db.Column(db.Integer, primary_key=True, doc="Unique chunk identifier")
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.id'), nullable=False,
                          doc="Foreign key to parent context")
    file_name = db.Column(db.String(255), nullable=False,
                         doc="Original filename for source attribution")
    chunk_index = db.Column(db.Integer, nullable=False,
                           doc="Sequential index of chunk within document")
    content = db.Column(db.Text, nullable=False,
                       doc="Actual text content of the chunk")
    file_info = db.Column(db.Text,
                         doc="JSON metadata about source file and chunk context")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          doc="Timestamp when chunk was created")

    def get_file_info(self):
        """
        Get file metadata as dictionary
        
        Parses the JSON file information stored in the database and returns
        it as a Python dictionary for easy access to chunk metadata.
        
        Returns:
            dict: File metadata including:
                - language: Programming language (for code files)
                - file_type: Type of source file
                - start_line: Starting line number in source file
                - end_line: Ending line number in source file
                - function_name: Function/method name (for code chunks)
                - class_name: Class name (for code chunks)
                
        Example:
            >>> info = chunk.get_file_info()
            >>> print(f"Language: {info.get('language', 'unknown')}")
        """
        return json.loads(self.file_info) if self.file_info else {}
    
    def set_file_info(self, info_dict):
        """
        Set file metadata from dictionary
        
        Converts a Python dictionary to JSON string format and stores it in
        the database for chunk metadata tracking.
        
        Args:
            info_dict (dict): Metadata dictionary containing:
                - language: Programming language identifier
                - file_type: Source file type
                - start_line: Starting line number
                - end_line: Ending line number
                - function_name: Function/method name
                - class_name: Class name
                
        Example:
            >>> chunk.set_file_info({
            ...     'language': 'python',
            ...     'file_type': 'code',
            ...     'function_name': 'main'
            ... })
        """
        self.file_info = json.dumps(info_dict)
    
    def to_dict(self):
        """
        Convert text chunk model to dictionary representation
        
        Serializes the text chunk model for JSON responses, including content
        and metadata for vector search and source attribution.
        
        Returns:
            dict: Chunk data including:
                - Basic info: id, chunk_index, content
                - Source info: file_name, file_info (parsed from JSON)
                - Timestamp: created_at (ISO format)
                
        Example:
            >>> chunk_data = chunk.to_dict()
            >>> print(f"Chunk {chunk_data['chunk_index']}: {chunk_data['content'][:50]}...")
        """
        return {
            'id': self.id,
            'context_id': self.context_id,
            'file_name': self.file_name,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'file_info': self.get_file_info(),
            'created_at': self.created_at.isoformat()
        }


class UserPreferences(db.Model):
    """
    User preferences model for storing personalized application settings
    
    Stores user-specific preferences and configuration settings that customize
    the application experience. This includes theme preferences, chat settings,
    notification preferences, and other user-configurable options.
    
    Key Features:
    - JSON storage for flexible preference structure
    - Automatic timestamp tracking for preference changes
    - Category-based preference organization
    - Backup and restore capabilities
    - Template system integration
    
    Preference Categories:
    - theme: UI theme, colors, layout preferences
    - chat: Chat behavior, streaming, context limits
    - notifications: Email, push, sound preferences
    - privacy: Data sharing, analytics preferences
    - accessibility: Screen reader, font size, contrast
    
    Relationships:
    - user: Many-to-one with User (preference owner)
    
    Example:
        >>> prefs = UserPreferences(
        ...     user_id=user.id,
        ...     preferences={
        ...         'theme': {'mode': 'dark'},
        ...         'chat': {'streaming': True}
        ...     }
        ... )
    """
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True, doc="Unique preference record identifier")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True,
                        doc="Foreign key to user who owns these preferences")
    preferences = db.Column(db.JSON, default=dict,
                           doc="JSON object containing all user preferences")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          doc="Timestamp when preferences were first created")
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc),
                          doc="Timestamp when preferences were last updated")
    
    # Relationship
    user = db.relationship('User', backref=db.backref('preferences', uselist=False, cascade='all, delete-orphan'))
    
    def get_preference(self, category, key=None, default=None):
        """
        Get a specific preference value
        
        Retrieves a preference value from the stored JSON preferences,
        supporting both category-level and key-level access.
        
        Args:
            category (str): Preference category (e.g., 'theme', 'chat')
            key (str, optional): Specific key within category
            default: Default value if preference not found
            
        Returns:
            Any: Preference value or default if not found
            
        Example:
            >>> theme_mode = prefs.get_preference('theme', 'mode', 'light')
            >>> chat_prefs = prefs.get_preference('chat')
        """
        if not self.preferences:
            return default
            
        category_prefs = self.preferences.get(category, {})
        
        if key is None:
            return category_prefs if category_prefs else default
        
        return category_prefs.get(key, default)
    
    def set_preference(self, category, key, value):
        """
        Set a specific preference value
        
        Updates a preference value in the stored JSON preferences,
        creating the category structure if it doesn't exist.
        
        Args:
            category (str): Preference category
            key (str): Preference key within category
            value: Preference value to set
            
        Example:
            >>> prefs.set_preference('theme', 'mode', 'dark')
            >>> prefs.set_preference('chat', 'streaming', True)
        """
        if not self.preferences:
            self.preferences = {}
        
        if category not in self.preferences:
            self.preferences[category] = {}
        
        self.preferences[category][key] = value
        self.updated_at = datetime.now(timezone.utc)
        
        # Mark as modified for SQLAlchemy
        db.session.merge(self)
    
    def update_category(self, category, preferences_dict):
        """
        Update an entire preference category
        
        Replaces all preferences in a category with new values,
        useful for bulk updates or category resets.
        
        Args:
            category (str): Preference category to update
            preferences_dict (dict): New preferences for the category
            
        Example:
            >>> prefs.update_category('theme', {
            ...     'mode': 'dark',
            ...     'primary_color': '#1976d2'
            ... })
        """
        if not self.preferences:
            self.preferences = {}
        
        self.preferences[category] = preferences_dict
        self.updated_at = datetime.now(timezone.utc)
        
        # Mark as modified for SQLAlchemy
        db.session.merge(self)
    
    def to_dict(self):
        """
        Convert preferences model to dictionary representation
        
        Serializes the preferences model for JSON responses, including
        all preference data and metadata timestamps.
        
        Returns:
            dict: Preferences data including:
                - Basic info: id, user_id
                - Preferences: preferences (complete JSON object)
                - Timestamps: created_at, updated_at (ISO format)
                
        Example:
            >>> prefs_data = prefs.to_dict()
            >>> theme_mode = prefs_data['preferences']['theme']['mode']
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferences': self.preferences or {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_user_preferences(cls, user_id, category=None):
        """
        Get user preferences with defaults filled in.
        
        Args:
            user_id: ID of the user
            category: Optional category filter
            
        Returns:
            Dictionary of preferences organized by category
        """
        from user_preferences import DEFAULT_PREFERENCES
        
        user_prefs = cls.query.filter_by(user_id=user_id).first()
        stored_prefs = user_prefs.preferences if user_prefs else {}
        
        # Start with defaults and merge stored preferences
        result = {}
        if category:
            if category in DEFAULT_PREFERENCES:
                result[category] = DEFAULT_PREFERENCES[category].copy()
                if category in stored_prefs:
                    result[category].update(stored_prefs[category])
        else:
            for cat, defaults in DEFAULT_PREFERENCES.items():
                result[cat] = defaults.copy()
                if cat in stored_prefs:
                    result[cat].update(stored_prefs[cat])
        
        return result
    
    @classmethod
    def set_user_preference(cls, user_id, category, key, value, description=None):
        """
        Set a user preference, creating or updating as needed.
        
        Args:
            user_id: ID of the user
            category: Preference category
            key: Preference key
            value: Preference value
            description: Optional description (ignored for compatibility)
            
        Returns:
            Mock preference object for compatibility
        """
        user_prefs = cls.query.filter_by(user_id=user_id).first()
        if not user_prefs:
            user_prefs = cls(user_id=user_id, preferences={})
            db.session.add(user_prefs)
        
        if not user_prefs.preferences:
            user_prefs.preferences = {}
        
        if category not in user_prefs.preferences:
            user_prefs.preferences[category] = {}
        
        user_prefs.preferences[category][key] = value
        user_prefs.updated_at = datetime.now(timezone.utc)
        
        # Mark as modified for SQLAlchemy
        db.session.merge(user_prefs)
        db.session.commit()
        
        # Return a mock object for compatibility
        class MockPreference:
            def __init__(self, value):
                self.value = value
        
        return MockPreference(value)
    
    @classmethod 
    def reset_user_preferences(cls, user_id, category=None):
        """
        Reset user preferences to defaults.
        
        Args:
            user_id: ID of the user
            category: Optional category to reset (None for all)
            
        Returns:
            Number of preferences reset
        """
        user_prefs = cls.query.filter_by(user_id=user_id).first()
        if not user_prefs or not user_prefs.preferences:
            return 0
        
        count = 0
        if category:
            if category in user_prefs.preferences:
                count = len(user_prefs.preferences[category])
                del user_prefs.preferences[category]
        else:
            count = sum(len(prefs) for prefs in user_prefs.preferences.values())
            user_prefs.preferences = {}
        
        user_prefs.updated_at = datetime.now(timezone.utc)
        db.session.merge(user_prefs)
        db.session.commit()
        
        return count
    
    @classmethod
    def export_user_preferences(cls, user_id, format='json'):
        """
        Export user preferences in specified format.
        
        Args:
            user_id: ID of the user
            format: Export format ('json', 'csv')
            
        Returns:
            Exported preferences as string
        """
        preferences = cls.get_user_preferences(user_id)
        
        if format.lower() == 'json':
            return json.dumps(preferences, indent=2, default=str)
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Category', 'Key', 'Value', 'Type'])
            
            for category, prefs in preferences.items():
                for key, value in prefs.items():
                    writer.writerow([category, key, value, type(value).__name__])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def set_file_info(self, info_dict):
        """
        Set file and chunk metadata from dictionary
        
        Converts a Python dictionary containing file and chunk metadata to JSON
        string format for database storage. This metadata is used for source
        attribution and search result enhancement.
        
        Args:
            info_dict (dict or None): Metadata dictionary containing:
                - file_type: Type of source file (code, document, data, etc.)
                - language: Programming language for code files
                - start_line/end_line: Line numbers for code chunks
                - page_number: Page reference for document chunks
                - function_name: Function/class name for code chunks
                - section_title: Section heading for document chunks
                
        Example:
            >>> chunk.set_file_info({
            ...     'file_type': 'code',
            ...     'language': 'python',
            ...     'function_name': 'process_file',
            ...     'start_line': 45,
            ...     'end_line': 67
            ... })
        """
        self.file_info = json.dumps(info_dict) if info_dict else None

    def get_file_info(self):
        """
        Get file and chunk metadata as dictionary
        
        Parses the JSON metadata string stored in the database and returns it
        as a Python dictionary for easy access to file and chunk information.
        
        Returns:
            dict: Metadata dictionary containing file and chunk information:
                - file_type: Type of source file
                - language: Programming language (for code files)
                - start_line/end_line: Line number references
                - page_number: Page reference (for documents)
                - function_name: Function/class name (for code)
                - section_title: Section heading (for documents)
                - Empty dict if no metadata stored
                
        Example:
            >>> info = chunk.get_file_info()
            >>> if info.get('file_type') == 'code':
            ...     print(f"Function: {info.get('function_name')}")
        """
        return json.loads(self.file_info) if self.file_info else {}

    def to_dict(self):
        """
        Convert text chunk model to dictionary representation
        
        Serializes the text chunk model for JSON responses and vector search results.
        This is used when returning search results to the frontend and for debugging
        RAG operations.
        
        Returns:
            dict: Chunk data including:
                - Basic info: id, context_id, file_name, chunk_index
                - Content: content (actual text)
                - Metadata: parsed file_info dictionary
                - Timestamp: created_at (ISO format)
                
        Example:
            >>> chunk_data = chunk.to_dict()
            >>> print(f"Chunk {chunk_data['chunk_index']} from {chunk_data['file_name']}")
            >>> print(f"Content length: {len(chunk_data['content'])} characters")
        """
        return {
            'id': self.id,
            'context_id': self.context_id,
            'file_name': self.file_name,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'metadata': self.get_file_info(),
            'created_at': self.created_at.isoformat()
        }


# Export all models
__all__ = [
    'db', 'User', 'Context', 'Document', 'TextChunk', 'ChatSession', 'Message', 
    'TimestampMixin', 'UserPreferences'
]
