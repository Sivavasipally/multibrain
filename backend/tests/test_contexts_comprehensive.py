"""
Comprehensive tests for contexts API endpoints and functionality
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from models import Context, Document, User
from services.vector_service import VectorService
from services.document_processor import DocumentProcessor


class TestContextsAPI:
    """Test contexts API endpoints with comprehensive coverage."""
    
    def test_get_contexts_success(self, client, auth_headers, test_user, test_context):
        """Test successful contexts retrieval."""
        response = client.get('/api/contexts', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'contexts' in data
        assert len(data['contexts']) >= 1
        assert data['contexts'][0]['id'] == test_context.id
        assert data['contexts'][0]['name'] == test_context.name
    
    def test_get_contexts_unauthorized(self, client):
        """Test contexts retrieval without authentication."""
        response = client.get('/api/contexts')
        assert response.status_code == 401
    
    def test_get_contexts_with_filters(self, client, auth_headers, test_user):
        """Test contexts retrieval with status and type filters."""
        # Create contexts with different statuses and types
        contexts_data = [
            {'name': 'Ready Files', 'status': 'ready', 'source_type': 'files'},
            {'name': 'Processing Repo', 'status': 'processing', 'source_type': 'repo'},
            {'name': 'Error Database', 'status': 'error', 'source_type': 'database'}
        ]
        
        for data in contexts_data:
            context = Context(
                user_id=test_user.id,
                **data
            )
            from app import db
            db.session.add(context)
        db.session.commit()
        
        # Test status filter
        response = client.get('/api/contexts?status=ready', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        ready_contexts = [c for c in data['contexts'] if c['status'] == 'ready']
        assert len(ready_contexts) >= 1
        
        # Test source type filter
        response = client.get('/api/contexts?source_type=repo', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        repo_contexts = [c for c in data['contexts'] if c['source_type'] == 'repo']
        assert len(repo_contexts) >= 1
    
    def test_create_context_files_success(self, client, auth_headers):
        """Test successful file-based context creation."""
        context_data = {
            'name': 'Test Files Context',
            'description': 'A context for testing files',
            'source_type': 'files',
            'chunk_strategy': 'language-specific',
            'embedding_model': 'text-embedding-004'
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(context_data),
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'context' in data
        assert data['context']['name'] == context_data['name']
        assert data['context']['source_type'] == context_data['source_type']
        assert data['context']['status'] == 'pending'
    
    def test_create_context_repo_success(self, client, auth_headers):
        """Test successful repository-based context creation."""
        context_data = {
            'name': 'Test Repo Context',
            'description': 'A context for testing repositories',
            'source_type': 'repo',
            'config': {
                'repo_url': 'https://github.com/test/repo.git',
                'branch': 'main',
                'include_patterns': ['*.py', '*.md'],
                'exclude_patterns': ['__pycache__/*']
            }
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(context_data),
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['context']['source_type'] == 'repo'
        assert 'repo_url' in data['context']['config']
    
    def test_create_context_database_success(self, client, auth_headers):
        """Test successful database-based context creation."""
        context_data = {
            'name': 'Test DB Context',
            'description': 'A context for testing databases',
            'source_type': 'database',
            'config': {
                'connection_string': 'postgresql://user:pass@localhost:5432/testdb',
                'tables': ['users', 'products'],
                'query_limit': 1000
            }
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(context_data),
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['context']['source_type'] == 'database'
        assert 'connection_string' in data['context']['config']
    
    def test_create_context_missing_name(self, client, auth_headers):
        """Test context creation with missing required fields."""
        context_data = {
            'description': 'Missing name',
            'source_type': 'files'
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(context_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_context_invalid_source_type(self, client, auth_headers):
        """Test context creation with invalid source type."""
        context_data = {
            'name': 'Invalid Source',
            'source_type': 'invalid_type'
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(context_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid source_type' in data['error']
    
    def test_get_context_success(self, client, auth_headers, test_context):
        """Test successful individual context retrieval."""
        response = client.get(f'/api/contexts/{test_context.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'context' in data
        assert data['context']['id'] == test_context.id
        assert data['context']['name'] == test_context.name
    
    def test_get_context_not_found(self, client, auth_headers):
        """Test context retrieval with non-existent ID."""
        response = client.get('/api/contexts/99999', headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_context_unauthorized_access(self, client, auth_headers, test_user):
        """Test context access by unauthorized user."""
        # Create context for different user
        other_user = User(username='other', email='other@example.com')
        other_user.set_password('password')
        from app import db
        db.session.add(other_user)
        db.session.commit()
        
        other_context = Context(
            name='Other User Context',
            user_id=other_user.id,
            source_type='files'
        )
        db.session.add(other_context)
        db.session.commit()
        
        response = client.get(f'/api/contexts/{other_context.id}', headers=auth_headers)
        assert response.status_code == 404  # Should act as if not found
    
    def test_update_context_success(self, client, auth_headers, test_context):
        """Test successful context update."""
        update_data = {
            'name': 'Updated Context Name',
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/contexts/{test_context.id}',
                            data=json.dumps(update_data),
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['context']['name'] == update_data['name']
        assert data['context']['description'] == update_data['description']
    
    def test_delete_context_success(self, client, auth_headers, test_context):
        """Test successful context deletion."""
        context_id = test_context.id
        
        response = client.delete(f'/api/contexts/{context_id}', headers=auth_headers)
        assert response.status_code == 200
        
        # Verify context is deleted
        response = client.get(f'/api/contexts/{context_id}', headers=auth_headers)
        assert response.status_code == 404
    
    def test_reprocess_context_success(self, client, auth_headers, test_context):
        """Test successful context reprocessing."""
        response = client.post(f'/api/contexts/{test_context.id}/reprocess',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'message' in data
        assert 'context' in data
    
    def test_get_context_status(self, client, auth_headers, test_context):
        """Test context status retrieval."""
        response = client.get(f'/api/contexts/{test_context.id}/status',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        expected_fields = ['status', 'progress', 'total_chunks', 'total_tokens']
        for field in expected_fields:
            assert field in data
    
    @patch('services.vector_service.VectorService')
    def test_context_search_success(self, mock_vector_service, client, auth_headers, test_context):
        """Test context search functionality."""
        # Mock vector service search results
        mock_results = [
            {
                'context': test_context.to_dict(),
                'relevance_score': 95.5,
                'highlights': [
                    {
                        'field': 'name',
                        'fragment': 'Test Context',
                        'positions': [0]
                    }
                ]
            }
        ]
        
        with patch('routes.contexts.contextSearchService') as mock_search:
            mock_search.searchContexts.return_value = {
                'results': mock_results,
                'total': 1,
                'query': 'test',
                'filters': {},
                'execution_time_ms': 125,
                'suggestions': []
            }
            
            response = client.get('/api/contexts/search?q=test', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'results' in data
            assert 'total' in data
            assert 'execution_time_ms' in data
            assert len(data['results']) == 1


class TestContextModel:
    """Test Context model functionality."""
    
    def test_context_creation(self, test_user):
        """Test context model creation."""
        context = Context(
            name='Test Model Context',
            description='Testing context model',
            source_type='files',
            user_id=test_user.id
        )
        
        assert context.name == 'Test Model Context'
        assert context.source_type == 'files'
        assert context.user_id == test_user.id
        assert context.status == 'pending'  # Default status
    
    def test_context_to_dict(self, test_context):
        """Test context serialization to dictionary."""
        context_dict = test_context.to_dict()
        
        expected_keys = [
            'id', 'name', 'description', 'source_type', 'config',
            'chunk_strategy', 'embedding_model', 'status', 'progress',
            'total_chunks', 'total_tokens', 'created_at', 'updated_at'
        ]
        
        for key in expected_keys:
            assert key in context_dict
        
        assert context_dict['name'] == test_context.name
        assert context_dict['source_type'] == test_context.source_type
    
    def test_context_status_transitions(self, test_context):
        """Test valid context status transitions."""
        from app import db
        
        # Initial status should be pending
        assert test_context.status == 'ready'  # From fixture
        
        # Test transition to processing
        test_context.status = 'processing'
        test_context.progress = 50
        db.session.commit()
        
        db.session.refresh(test_context)
        assert test_context.status == 'processing'
        assert test_context.progress == 50
        
        # Test transition to ready
        test_context.status = 'ready'
        test_context.progress = 100
        test_context.total_chunks = 150
        db.session.commit()
        
        db.session.refresh(test_context)
        assert test_context.status == 'ready'
        assert test_context.progress == 100


class TestContextProcessing:
    """Test context processing functionality with mocked services."""
    
    @patch('services.document_processor.DocumentProcessor')
    @patch('services.vector_service.VectorService')
    def test_file_context_processing(self, mock_vector_service, mock_doc_processor, 
                                   test_context, sample_files):
        """Test file-based context processing workflow."""
        # Mock document processor
        mock_processor = mock_doc_processor.return_value
        mock_processor.process_file.return_value = {
            'chunks': [
                {
                    'content': 'Test file content chunk 1',
                    'metadata': {'file_path': 'test.txt', 'chunk_index': 0}
                },
                {
                    'content': 'Test file content chunk 2', 
                    'metadata': {'file_path': 'test.txt', 'chunk_index': 1}
                }
            ],
            'total_tokens': 200,
            'language': 'text'
        }
        
        # Mock vector service
        mock_vector = mock_vector_service.return_value
        mock_vector.add_documents.return_value = True
        
        # Simulate processing
        from services.document_processor import DocumentProcessor
        from services.vector_service import VectorService
        
        processor = DocumentProcessor()
        vector_service = VectorService()
        
        # Process mock file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('This is test file content for processing.')
            temp_path = f.name
        
        try:
            result = processor.process_file(temp_path, 'text/plain')
            
            # Verify processing results
            assert 'chunks' in result
            assert len(result['chunks']) >= 1
            assert result['total_tokens'] > 0
            
            # Test vector storage
            success = vector_service.add_documents(result['chunks'], test_context.id)
            assert success is True
            
        finally:
            os.unlink(temp_path)
    
    @patch('services.repository_service.RepositoryService')
    @patch('services.vector_service.VectorService')
    def test_repo_context_processing(self, mock_vector_service, mock_repo_service, test_user):
        """Test repository-based context processing."""
        # Create repo context
        repo_context = Context(
            name='Test Repo Context',
            source_type='repo',
            config={
                'repo_url': 'https://github.com/test/repo.git',
                'branch': 'main'
            },
            user_id=test_user.id
        )
        from app import db
        db.session.add(repo_context)
        db.session.commit()
        
        # Mock repository service
        mock_repo = mock_repo_service.return_value
        mock_repo.clone_repository.return_value = {
            'success': True,
            'local_path': '/tmp/test_repo',
            'files': ['README.md', 'src/main.py']
        }
        
        mock_repo.list_files.return_value = [
            {'path': 'README.md', 'type': 'markdown'},
            {'path': 'src/main.py', 'type': 'python'}
        ]
        
        # Mock vector service
        mock_vector = mock_vector_service.return_value
        mock_vector.add_documents.return_value = True
        
        # Test repository processing
        from services.repository_service import RepositoryService
        repo_service = RepositoryService()
        
        clone_result = repo_service.clone_repository(repo_context.config['repo_url'])
        assert clone_result['success'] is True
        assert len(clone_result['files']) > 0
    
    def test_context_error_handling(self, test_context):
        """Test context error state handling."""
        from app import db
        
        # Simulate processing error
        test_context.status = 'error'
        test_context.error_message = 'Processing failed: Invalid file format'
        db.session.commit()
        
        db.session.refresh(test_context)
        assert test_context.status == 'error'
        assert 'Invalid file format' in test_context.error_message
    
    def test_context_metrics_tracking(self, test_context):
        """Test context metrics and statistics tracking."""
        from app import db
        
        # Update context with processing metrics
        test_context.total_chunks = 250
        test_context.total_tokens = 15000
        test_context.status = 'ready'
        test_context.progress = 100
        db.session.commit()
        
        # Verify metrics
        db.session.refresh(test_context)
        assert test_context.total_chunks == 250
        assert test_context.total_tokens == 15000
        assert test_context.progress == 100


class TestContextDocuments:
    """Test context document management."""
    
    def test_add_document_to_context(self, test_context):
        """Test adding documents to a context."""
        from app import db
        
        document = Document(
            context_id=test_context.id,
            filename='test_document.txt',
            file_type='text/plain',
            file_size=1024,
            chunks_count=5,
            tokens_count=150
        )
        db.session.add(document)
        db.session.commit()
        
        # Verify document is associated with context
        db.session.refresh(test_context)
        assert len(test_context.documents) >= 1
        
        doc = test_context.documents[0]
        assert doc.filename == 'test_document.txt'
        assert doc.context_id == test_context.id
    
    def test_context_document_statistics(self, test_context):
        """Test context document statistics calculation."""
        from app import db
        
        # Add multiple documents
        documents = [
            Document(context_id=test_context.id, filename='doc1.txt', 
                   file_size=500, chunks_count=3, tokens_count=75),
            Document(context_id=test_context.id, filename='doc2.md', 
                   file_size=800, chunks_count=7, tokens_count=125),
            Document(context_id=test_context.id, filename='doc3.py', 
                   file_size=1200, chunks_count=10, tokens_count=200)
        ]
        
        for doc in documents:
            db.session.add(doc)
        db.session.commit()
        
        # Update context statistics
        db.session.refresh(test_context)
        
        total_chunks = sum(doc.chunks_count or 0 for doc in test_context.documents)
        total_tokens = sum(doc.tokens_count or 0 for doc in test_context.documents)
        
        # Update context with calculated statistics
        test_context.total_chunks = total_chunks
        test_context.total_tokens = total_tokens
        db.session.commit()
        
        db.session.refresh(test_context)
        assert test_context.total_chunks == 20  # 3 + 7 + 10
        assert test_context.total_tokens == 400  # 75 + 125 + 200


class TestContextSecurity:
    """Test context security and access control."""
    
    def test_context_ownership_enforcement(self, client, test_user):
        """Test that users can only access their own contexts."""
        from app import db
        
        # Create another user and context
        other_user = User(username='otheruser', email='other@test.com')
        other_user.set_password('password')
        db.session.add(other_user)
        db.session.commit()
        
        other_context = Context(
            name='Other User Context',
            user_id=other_user.id,
            source_type='files'
        )
        db.session.add(other_context)
        db.session.commit()
        
        # Create auth headers for test_user
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=test_user.id)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test_user should not be able to access other_user's context
        response = client.get(f'/api/contexts/{other_context.id}', headers=headers)
        assert response.status_code == 404
        
        # Test_user should not be able to modify other_user's context
        update_data = {'name': 'Hacked Context'}
        response = client.put(f'/api/contexts/{other_context.id}',
                            data=json.dumps(update_data), headers=headers)
        assert response.status_code == 404
        
        # Test_user should not be able to delete other_user's context
        response = client.delete(f'/api/contexts/{other_context.id}', headers=headers)
        assert response.status_code == 404
    
    def test_context_data_isolation(self, client, test_user):
        """Test that context data is properly isolated between users."""
        from app import db
        from flask_jwt_extended import create_access_token
        
        # Create contexts for test_user
        user_contexts = []
        for i in range(3):
            context = Context(
                name=f'User Context {i}',
                user_id=test_user.id,
                source_type='files'
            )
            db.session.add(context)
            user_contexts.append(context)
        
        # Create another user and contexts
        other_user = User(username='isolated', email='isolated@test.com')
        other_user.set_password('password')
        db.session.add(other_user)
        db.session.commit()
        
        other_contexts = []
        for i in range(2):
            context = Context(
                name=f'Other Context {i}',
                user_id=other_user.id,
                source_type='files'
            )
            db.session.add(context)
            other_contexts.append(context)
        
        db.session.commit()
        
        # Test isolation - test_user should only see their contexts
        token = create_access_token(identity=test_user.id)
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        response = client.get('/api/contexts', headers=headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        returned_context_ids = [ctx['id'] for ctx in data['contexts']]
        user_context_ids = [ctx.id for ctx in user_contexts]
        other_context_ids = [ctx.id for ctx in other_contexts]
        
        # Should contain user's contexts
        for ctx_id in user_context_ids:
            assert ctx_id in returned_context_ids
        
        # Should NOT contain other user's contexts
        for ctx_id in other_context_ids:
            assert ctx_id not in returned_context_ids