"""
Tests for context management endpoints
"""

import pytest
import json
from models import Context


class TestContextEndpoints:
    """Test context management endpoints."""
    
    def test_get_contexts_empty(self, client, auth_headers):
        """Test getting contexts when none exist."""
        response = client.get('/api/contexts', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'contexts' in response_data
        assert response_data['contexts'] == []
    
    def test_get_contexts_with_data(self, client, auth_headers, test_context):
        """Test getting contexts when they exist."""
        response = client.get('/api/contexts', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'contexts' in response_data
        assert len(response_data['contexts']) == 1
        
        context = response_data['contexts'][0]
        assert context['id'] == test_context.id
        assert context['name'] == test_context.name
        assert context['source_type'] == test_context.source_type
    
    def test_get_contexts_unauthorized(self, client):
        """Test getting contexts without authentication."""
        response = client.get('/api/contexts')
        
        assert response.status_code == 401
    
    def test_create_context_success(self, client, auth_headers):
        """Test successful context creation."""
        data = {
            'name': 'New Test Context',
            'description': 'A new context for testing',
            'source_type': 'files',
            'chunk_strategy': 'language-specific',
            'embedding_model': 'text-embedding-004',
            'config': {
                'file_paths': ['test1.txt', 'test2.py']
            }
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(data),
                             headers=auth_headers)
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        
        assert 'context' in response_data
        context = response_data['context']
        
        assert context['name'] == data['name']
        assert context['description'] == data['description']
        assert context['source_type'] == data['source_type']
        assert context['config'] == data['config']
        assert context['status'] in ['pending', 'ready']  # Depends on implementation
    
    def test_create_context_missing_name(self, client, auth_headers):
        """Test context creation with missing name."""
        data = {
            'description': 'A context without name',
            'source_type': 'files'
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(data),
                             headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_create_context_invalid_source_type(self, client, auth_headers):
        """Test context creation with invalid source type."""
        data = {
            'name': 'Invalid Context',
            'source_type': 'invalid_type'
        }
        
        response = client.post('/api/contexts',
                             data=json.dumps(data),
                             headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_get_context_by_id(self, client, auth_headers, test_context):
        """Test getting a specific context by ID."""
        response = client.get(f'/api/contexts/{test_context.id}', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'context' in response_data
        context = response_data['context']
        
        assert context['id'] == test_context.id
        assert context['name'] == test_context.name
    
    def test_get_context_not_found(self, client, auth_headers):
        """Test getting a non-existent context."""
        response = client.get('/api/contexts/999', headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_context_unauthorized(self, client, test_context):
        """Test getting context without authentication."""
        response = client.get(f'/api/contexts/{test_context.id}')
        
        assert response.status_code == 401
    
    def test_update_context(self, client, auth_headers, test_context):
        """Test updating a context."""
        update_data = {
            'name': 'Updated Context Name',
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/contexts/{test_context.id}',
                            data=json.dumps(update_data),
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'context' in response_data
        context = response_data['context']
        
        assert context['name'] == update_data['name']
        assert context['description'] == update_data['description']
    
    def test_update_context_not_found(self, client, auth_headers):
        """Test updating a non-existent context."""
        update_data = {
            'name': 'Updated Name'
        }
        
        response = client.put('/api/contexts/999',
                            data=json.dumps(update_data),
                            headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_delete_context(self, client, auth_headers, test_context):
        """Test deleting a context."""
        response = client.delete(f'/api/contexts/{test_context.id}', headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify context is deleted
        get_response = client.get(f'/api/contexts/{test_context.id}', headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_context_not_found(self, client, auth_headers):
        """Test deleting a non-existent context."""
        response = client.delete('/api/contexts/999', headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_reprocess_context(self, client, auth_headers, test_context):
        """Test reprocessing a context."""
        response = client.post(f'/api/contexts/{test_context.id}/reprocess', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'context' in response_data
        # Status should be updated to processing or pending
        assert response_data['context']['status'] in ['processing', 'pending']
    
    def test_get_context_status(self, client, auth_headers, test_context):
        """Test getting context processing status."""
        response = client.get(f'/api/contexts/{test_context.id}/status', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        expected_keys = ['status', 'progress', 'total_chunks', 'total_tokens']
        for key in expected_keys:
            assert key in response_data


class TestContextModel:
    """Test Context model functionality."""
    
    def test_context_creation(self, test_user):
        """Test context model creation."""
        context = Context(
            name='Test Context',
            description='A test context',
            source_type='files',
            user_id=test_user.id
        )
        
        assert context.name == 'Test Context'
        assert context.description == 'A test context'
        assert context.source_type == 'files'
        assert context.user_id == test_user.id
        assert context.status == 'pending'  # Default status
        assert context.progress == 0  # Default progress
    
    def test_context_config_handling(self, test_user):
        """Test context configuration JSON handling."""
        context = Context(
            name='Config Test',
            source_type='repo',
            user_id=test_user.id
        )
        
        # Test setting config
        config_data = {
            'repo_url': 'https://github.com/test/repo',
            'branch': 'main',
            'access_token': 'token123'
        }
        
        context.set_config(config_data)
        assert context.config is not None
        
        # Test getting config
        retrieved_config = context.get_config()
        assert retrieved_config == config_data
        assert retrieved_config['repo_url'] == 'https://github.com/test/repo'
    
    def test_context_to_dict(self, test_context):
        """Test context serialization to dictionary."""
        context_dict = test_context.to_dict()
        
        expected_keys = [
            'id', 'name', 'description', 'source_type', 'config',
            'status', 'progress', 'error_message', 'total_chunks',
            'total_tokens', 'created_at', 'updated_at'
        ]
        
        for key in expected_keys:
            assert key in context_dict
        
        assert context_dict['name'] == test_context.name
        assert context_dict['source_type'] == test_context.source_type
        assert isinstance(context_dict['config'], dict)


class TestContextIntegration:
    """Integration tests for context management."""
    
    def test_context_lifecycle(self, client, auth_headers):
        """Test complete context lifecycle: create -> update -> delete."""
        # 1. Create context
        create_data = {
            'name': 'Lifecycle Test Context',
            'description': 'Testing full lifecycle',
            'source_type': 'files',
            'config': {
                'file_paths': ['test.txt']
            }
        }
        
        create_response = client.post('/api/contexts',
                                    data=json.dumps(create_data),
                                    headers=auth_headers)
        
        assert create_response.status_code == 201
        create_response_data = json.loads(create_response.data)
        context_id = create_response_data['context']['id']
        
        # 2. Get context
        get_response = client.get(f'/api/contexts/{context_id}', headers=auth_headers)
        assert get_response.status_code == 200
        
        # 3. Update context
        update_data = {
            'name': 'Updated Lifecycle Context',
            'description': 'Updated description'
        }
        
        update_response = client.put(f'/api/contexts/{context_id}',
                                   data=json.dumps(update_data),
                                   headers=auth_headers)
        
        assert update_response.status_code == 200
        update_response_data = json.loads(update_response.data)
        assert update_response_data['context']['name'] == update_data['name']
        
        # 4. Delete context
        delete_response = client.delete(f'/api/contexts/{context_id}', headers=auth_headers)
        assert delete_response.status_code == 200
        
        # 5. Verify deletion
        final_get_response = client.get(f'/api/contexts/{context_id}', headers=auth_headers)
        assert final_get_response.status_code == 404
    
    def test_multiple_contexts_isolation(self, client, auth_headers, test_user):
        """Test that contexts are properly isolated between users."""
        # Create another user
        other_user_data = {
            'username': 'otheruser',
            'email': 'other@example.com',
            'password': 'password123'
        }
        
        register_response = client.post('/api/auth/register',
                                      data=json.dumps(other_user_data),
                                      content_type='application/json')
        
        assert register_response.status_code == 201
        other_user_token = json.loads(register_response.data)['access_token']
        
        other_headers = {
            'Authorization': f'Bearer {other_user_token}',
            'Content-Type': 'application/json'
        }
        
        # Create context for first user
        context1_data = {
            'name': 'User 1 Context',
            'source_type': 'files'
        }
        
        response1 = client.post('/api/contexts',
                              data=json.dumps(context1_data),
                              headers=auth_headers)
        assert response1.status_code == 201
        
        # Create context for second user
        context2_data = {
            'name': 'User 2 Context',
            'source_type': 'repo'
        }
        
        response2 = client.post('/api/contexts',
                              data=json.dumps(context2_data),
                              headers=other_headers)
        assert response2.status_code == 201
        
        # Each user should only see their own contexts
        user1_contexts = client.get('/api/contexts', headers=auth_headers)
        user1_data = json.loads(user1_contexts.data)
        assert len(user1_data['contexts']) == 1
        assert user1_data['contexts'][0]['name'] == 'User 1 Context'
        
        user2_contexts = client.get('/api/contexts', headers=other_headers)
        user2_data = json.loads(user2_contexts.data)
        assert len(user2_data['contexts']) == 1
        assert user2_data['contexts'][0]['name'] == 'User 2 Context'
