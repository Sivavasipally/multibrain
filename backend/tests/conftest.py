"""
Test configuration and fixtures for the RAG Chatbot PWA backend
"""

import pytest
import tempfile
import os
from app import app, db
from models import User, Context, ChatSession, Message
from flask_jwt_extended import create_access_token


@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    # Create a temporary database file
    db_fd, app.config['DATABASE_URI'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_URI']
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            
    os.close(db_fd)
    os.unlink(app.config['DATABASE_URI'])


@pytest.fixture
def test_user():
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test requests."""
    access_token = create_access_token(identity=test_user.id)
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def test_context(test_user):
    """Create a test context."""
    context = Context(
        name='Test Context',
        description='A test context for unit tests',
        source_type='files',
        config='{"test": true}',
        status='ready',
        user_id=test_user.id
    )
    db.session.add(context)
    db.session.commit()
    return context


@pytest.fixture
def test_chat_session(test_user):
    """Create a test chat session."""
    session = ChatSession(
        title='Test Chat Session',
        user_id=test_user.id
    )
    db.session.add(session)
    db.session.commit()
    return session


@pytest.fixture
def test_message(test_chat_session):
    """Create a test message."""
    message = Message(
        session_id=test_chat_session.id,
        role='user',
        content='Test message content',
        context_ids='[1, 2]'
    )
    db.session.add(message)
    db.session.commit()
    return message


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        'candidates': [{
            'content': {
                'parts': [{
                    'text': 'This is a mock response from Gemini AI.'
                }]
            }
        }]
    }


@pytest.fixture
def sample_files():
    """Create sample files for testing uploads."""
    files = {
        'text_file': ('test.txt', b'This is a test file content', 'text/plain'),
        'json_file': ('test.json', b'{"test": "data"}', 'application/json'),
        'python_file': ('test.py', b'print("Hello, World!")', 'text/x-python'),
    }
    return files


@pytest.fixture
def mock_vector_service():
    """Mock vector service for testing."""
    class MockVectorService:
        def __init__(self):
            self.vectors = {}
            
        def add_documents(self, documents, context_id):
            self.vectors[context_id] = documents
            return True
            
        def search(self, query, context_ids, top_k=5):
            results = []
            for context_id in context_ids:
                if context_id in self.vectors:
                    for doc in self.vectors[context_id][:top_k]:
                        results.append({
                            'content': doc.get('content', ''),
                            'metadata': doc.get('metadata', {}),
                            'score': 0.9
                        })
            return results
            
        def delete_context(self, context_id):
            if context_id in self.vectors:
                del self.vectors[context_id]
            return True
    
    return MockVectorService()


@pytest.fixture
def mock_document_processor():
    """Mock document processor for testing."""
    class MockDocumentProcessor:
        def process_file(self, file_path, file_type):
            return {
                'chunks': [
                    {
                        'content': f'Mock processed content from {file_path}',
                        'metadata': {
                            'file_path': file_path,
                            'file_type': file_type,
                            'chunk_index': 0
                        }
                    }
                ],
                'total_tokens': 100,
                'language': 'text'
            }
            
        def extract_text(self, file_path):
            return f'Mock extracted text from {file_path}'
            
        def chunk_text(self, text, strategy='fixed-size'):
            return [
                {
                    'content': text[:100] if len(text) > 100 else text,
                    'metadata': {'chunk_index': 0}
                }
            ]
    
    return MockDocumentProcessor()


@pytest.fixture
def mock_repository_service():
    """Mock repository service for testing."""
    class MockRepositoryService:
        def clone_repository(self, repo_url, access_token=None):
            return {
                'success': True,
                'local_path': '/tmp/mock_repo',
                'files': ['README.md', 'src/main.py', 'tests/test_main.py']
            }
            
        def get_repository_info(self, repo_url, access_token=None):
            return {
                'name': 'mock-repo',
                'description': 'A mock repository for testing',
                'language': 'Python',
                'size': 1024,
                'files_count': 10
            }
            
        def list_files(self, repo_path, extensions=None):
            files = [
                {'path': 'README.md', 'type': 'markdown'},
                {'path': 'src/main.py', 'type': 'python'},
                {'path': 'tests/test_main.py', 'type': 'python'}
            ]
            
            if extensions:
                files = [f for f in files if f['type'] in extensions]
                
            return files
    
    return MockRepositoryService()


@pytest.fixture
def mock_database_service():
    """Mock database service for testing."""
    class MockDatabaseService:
        def test_connection(self, connection_string):
            return {
                'success': True,
                'message': 'Connection successful'
            }
            
        def get_schema(self, connection_string):
            return {
                'tables': [
                    {
                        'name': 'users',
                        'columns': [
                            {'name': 'id', 'type': 'INTEGER'},
                            {'name': 'username', 'type': 'VARCHAR'},
                            {'name': 'email', 'type': 'VARCHAR'}
                        ]
                    },
                    {
                        'name': 'products',
                        'columns': [
                            {'name': 'id', 'type': 'INTEGER'},
                            {'name': 'name', 'type': 'VARCHAR'},
                            {'name': 'price', 'type': 'DECIMAL'}
                        ]
                    }
                ]
            }
            
        def extract_data(self, connection_string, tables=None):
            return {
                'success': True,
                'data': {
                    'users': [
                        {'id': 1, 'username': 'john', 'email': 'john@example.com'},
                        {'id': 2, 'username': 'jane', 'email': 'jane@example.com'}
                    ],
                    'products': [
                        {'id': 1, 'name': 'Product A', 'price': 19.99},
                        {'id': 2, 'name': 'Product B', 'price': 29.99}
                    ]
                }
            }
    
    return MockDatabaseService()


# Test data constants
TEST_USER_DATA = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'testpassword123'
}

TEST_CONTEXT_DATA = {
    'name': 'Test Context',
    'description': 'A context for testing',
    'source_type': 'files',
    'chunk_strategy': 'language-specific',
    'embedding_model': 'text-embedding-004'
}

TEST_CHAT_DATA = {
    'title': 'Test Chat Session'
}

TEST_MESSAGE_DATA = {
    'message': 'What is the main purpose of this codebase?',
    'context_ids': [1],
    'stream': False
}
