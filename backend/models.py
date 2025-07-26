"""
Database models for RAG Chatbot PWA
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Initialize db here to avoid circular imports
db = SQLAlchemy()

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # OAuth fields
    github_id = db.Column(db.String(50), unique=True, nullable=True)
    bitbucket_id = db.Column(db.String(50), unique=True, nullable=True)
    
    # Relationships
    contexts = db.relationship('Context', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

class Context(db.Model):
    """Context model for RAG knowledge bases"""
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
        """Get configuration as dictionary"""
        return json.loads(self.config) if self.config else {}
    
    def set_config(self, config_dict):
        """Set configuration from dictionary"""
        self.config = json.dumps(config_dict)
    
    def to_dict(self):
        """Convert to dictionary"""
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
    """Document model for tracking processed files"""
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
        """Convert to dictionary"""
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
    """Chat session model"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }

class Message(db.Model):
    """Message model for chat history"""
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
        """Get context IDs as list"""
        return json.loads(self.context_ids) if self.context_ids else []
    
    def set_context_ids(self, context_list):
        """Set context IDs from list"""
        self.context_ids = json.dumps(context_list)
    
    def get_citations(self):
        """Get citations as list"""
        return json.loads(self.citations) if self.citations else []
    
    def set_citations(self, citations_list):
        """Set citations from list"""
        self.citations = json.dumps(citations_list)
    
    def to_dict(self):
        """Convert to dictionary"""
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
    """Text chunk model for storing processed document chunks"""
    __tablename__ = 'text_chunks'

    id = db.Column(db.Integer, primary_key=True)
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_info = db.Column(db.Text)  # JSON string for file information
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_file_info(self, info_dict):
        """Set file information from dictionary"""
        self.file_info = json.dumps(info_dict) if info_dict else None

    def get_file_info(self):
        """Get file information as dictionary"""
        return json.loads(self.file_info) if self.file_info else {}

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'context_id': self.context_id,
            'file_name': self.file_name,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'metadata': self.get_file_info(),
            'created_at': self.created_at.isoformat()
        }
