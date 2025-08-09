"""
Comprehensive tests for chat functionality
"""

import pytest
import json
from unittest.mock import patch, Mock
from models import ChatSession, Message, Context
from services.llm_service import LLMService


class TestChatSessions:
    """Test chat session management."""
    
    def test_create_chat_session_success(self, client, auth_headers):
        """Test successful chat session creation."""
        response = client.post('/api/chat/sessions', headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'session' in data
        assert 'id' in data['session']
        assert 'title' in data['session']
        assert data['session']['message_count'] == 0
    
    def test_get_chat_sessions(self, client, auth_headers, test_chat_session):
        """Test retrieving chat sessions."""
        response = client.get('/api/chat/sessions', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'sessions' in data
        assert len(data['sessions']) >= 1
        
        session = next(s for s in data['sessions'] if s['id'] == test_chat_session.id)
        assert session['title'] == test_chat_session.title
    
    def test_get_chat_session_by_id(self, client, auth_headers, test_chat_session):
        """Test retrieving specific chat session."""
        response = client.get(f'/api/chat/sessions/{test_chat_session.id}', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'session' in data
        assert data['session']['id'] == test_chat_session.id
        assert data['session']['title'] == test_chat_session.title
    
    def test_update_chat_session(self, client, auth_headers, test_chat_session):
        """Test updating chat session title."""
        update_data = {
            'title': 'Updated Chat Session Title'
        }
        
        response = client.put(f'/api/chat/sessions/{test_chat_session.id}',
                            data=json.dumps(update_data),
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['session']['title'] == update_data['title']
    
    def test_delete_chat_session(self, client, auth_headers, test_chat_session):
        """Test deleting chat session."""
        session_id = test_chat_session.id
        
        response = client.delete(f'/api/chat/sessions/{session_id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify session is deleted
        response = client.get(f'/api/chat/sessions/{session_id}',
                            headers=auth_headers)
        assert response.status_code == 404
    
    def test_chat_session_unauthorized_access(self, client, test_user):
        """Test accessing chat session without proper authorization."""
        from app import db
        from models import User
        from flask_jwt_extended import create_access_token
        
        # Create another user and session
        other_user = User(username='other', email='other@test.com')
        other_user.set_password('password')
        db.session.add(other_user)
        db.session.commit()
        
        other_session = ChatSession(
            title='Other User Session',
            user_id=other_user.id
        )
        db.session.add(other_session)
        db.session.commit()
        
        # Try to access with test_user credentials
        token = create_access_token(identity=test_user.id)
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        response = client.get(f'/api/chat/sessions/{other_session.id}',
                            headers=headers)
        assert response.status_code == 404


class TestChatMessages:
    """Test chat message functionality."""
    
    @patch('services.llm_service.LLMService.generate_response')
    @patch('services.vector_service.VectorService.search')
    def test_send_message_success(self, mock_vector_search, mock_llm_generate,
                                client, auth_headers, test_chat_session, test_context):
        """Test successful message sending with AI response."""
        # Mock vector search results
        mock_vector_search.return_value = [
            {
                'content': 'This is relevant context content.',
                'metadata': {'source': 'test.txt', 'chunk_id': '1'},
                'score': 0.95
            }
        ]
        
        # Mock LLM response
        mock_llm_generate.return_value = {
            'content': 'This is an AI-generated response based on the context.',
            'citations': [
                {
                    'source': 'test.txt',
                    'content': 'This is relevant context content.',
                    'score': 0.95
                }
            ],
            'tokens_used': 150
        }
        
        message_data = {
            'message': 'What is the main topic discussed in the documents?',
            'context_ids': [test_context.id]
        }
        
        response = client.post(f'/api/chat/{test_chat_session.id}',
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'message' in data
        assert data['message']['role'] == 'assistant'
        assert 'content' in data['message']
        assert 'citations' in data['message']
        assert len(data['message']['citations']) > 0
    
    def test_send_message_without_context(self, client, auth_headers, test_chat_session):
        """Test sending message without context selection."""
        message_data = {
            'message': 'Hello, how are you?',
            'context_ids': []
        }
        
        response = client.post(f'/api/chat/{test_chat_session.id}',
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'context_ids' in data['error']
    
    def test_send_empty_message(self, client, auth_headers, test_chat_session, test_context):
        """Test sending empty message."""
        message_data = {
            'message': '',
            'context_ids': [test_context.id]
        }
        
        response = client.post(f'/api/chat/{test_chat_session.id}',
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Message cannot be empty' in data['error']
    
    def test_get_chat_history(self, client, auth_headers, test_chat_session, test_message):
        """Test retrieving chat history."""
        response = client.get(f'/api/chat/{test_chat_session.id}/history',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'messages' in data
        assert len(data['messages']) >= 1
        
        message = next(m for m in data['messages'] if m['id'] == test_message.id)
        assert message['content'] == test_message.content
        assert message['role'] == test_message.role
    
    def test_message_context_validation(self, client, auth_headers, test_chat_session, test_user):
        """Test message with invalid context IDs."""
        from app import db
        
        message_data = {
            'message': 'Test with invalid context',
            'context_ids': [99999]  # Non-existent context ID
        }
        
        response = client.post(f'/api/chat/{test_chat_session.id}',
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid context' in data['error']
    
    @patch('services.llm_service.LLMService.generate_response')
    def test_message_streaming_response(self, mock_llm_generate,
                                      client, auth_headers, test_chat_session, test_context):
        """Test streaming message response."""
        # Mock streaming LLM response
        def mock_stream_generator():
            chunks = [
                'This is ',
                'a streaming ',
                'response from ',
                'the AI model.'
            ]
            for chunk in chunks:
                yield {'content': chunk, 'done': False}
            yield {'content': '', 'done': True, 'citations': []}
        
        mock_llm_generate.return_value = mock_stream_generator()
        
        message_data = {
            'message': 'Tell me about the project structure.',
            'context_ids': [test_context.id],
            'stream': True
        }
        
        response = client.post(f'/api/chat/{test_chat_session.id}',
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        # Note: Testing streaming responses requires special handling
        # This is a simplified test - full streaming tests would use Server-Sent Events
    
    def test_message_with_file_references(self, client, auth_headers, 
                                        test_chat_session, test_context):
        """Test message handling with file references."""
        from app import db
        from models import Document
        
        # Create test document
        document = Document(
            context_id=test_context.id,
            filename='reference.txt',
            file_type='text/plain',
            chunks_count=5
        )
        db.session.add(document)
        db.session.commit()
        
        with patch('services.vector_service.VectorService.search') as mock_search:
            mock_search.return_value = [
                {
                    'content': 'File content from reference.txt',
                    'metadata': {
                        'source': 'reference.txt',
                        'document_id': document.id
                    },
                    'score': 0.98
                }
            ]
            
            with patch('services.llm_service.LLMService.generate_response') as mock_llm:
                mock_llm.return_value = {
                    'content': 'Based on reference.txt, here is the answer.',
                    'citations': [
                        {
                            'source': 'reference.txt',
                            'document_id': document.id,
                            'content': 'File content from reference.txt',
                            'score': 0.98
                        }
                    ]
                }
                
                message_data = {
                    'message': 'What does reference.txt contain?',
                    'context_ids': [test_context.id]
                }
                
                response = client.post(f'/api/chat/{test_chat_session.id}',
                                     data=json.dumps(message_data),
                                     headers=auth_headers)
                
                assert response.status_code == 200
                data = json.loads(response.data)
                
                citations = data['message']['citations']
                assert len(citations) > 0
                assert citations[0]['source'] == 'reference.txt'
                assert citations[0]['document_id'] == document.id


class TestChatIntegration:
    """Integration tests for chat functionality."""
    
    @patch('services.llm_service.LLMService.generate_response')
    @patch('services.vector_service.VectorService.search')
    def test_complete_chat_flow(self, mock_vector_search, mock_llm_generate,
                              client, auth_headers, test_context):
        """Test complete chat flow from session creation to multiple messages."""
        # Mock services
        mock_vector_search.return_value = [
            {
                'content': 'Relevant context for the conversation.',
                'metadata': {'source': 'context.txt'},
                'score': 0.9
            }
        ]
        
        mock_llm_generate.return_value = {
            'content': 'AI response to user query.',
            'citations': [
                {
                    'source': 'context.txt',
                    'content': 'Relevant context for the conversation.',
                    'score': 0.9
                }
            ]
        }
        
        # 1. Create chat session
        response = client.post('/api/chat/sessions', headers=auth_headers)
        assert response.status_code == 201
        
        session_data = json.loads(response.data)
        session_id = session_data['session']['id']
        
        # 2. Send first message
        message1_data = {
            'message': 'What is this project about?',
            'context_ids': [test_context.id]
        }
        
        response = client.post(f'/api/chat/{session_id}',
                             data=json.dumps(message1_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        message1_response = json.loads(response.data)
        assert message1_response['message']['role'] == 'assistant'
        
        # 3. Send follow-up message
        message2_data = {
            'message': 'Can you provide more details?',
            'context_ids': [test_context.id]
        }
        
        response = client.post(f'/api/chat/{session_id}',
                             data=json.dumps(message2_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        
        # 4. Get chat history
        response = client.get(f'/api/chat/{session_id}/history',
                            headers=auth_headers)
        
        assert response.status_code == 200
        history_data = json.loads(response.data)
        
        # Should have 4 messages: 2 user messages + 2 assistant responses
        assert len(history_data['messages']) == 4
        
        # Check message ordering (should be chronological)
        messages = history_data['messages']
        assert messages[0]['role'] == 'user'
        assert messages[1]['role'] == 'assistant'
        assert messages[2]['role'] == 'user'
        assert messages[3]['role'] == 'assistant'
    
    def test_multi_context_conversation(self, client, auth_headers, test_user):
        """Test conversation using multiple contexts."""
        from app import db
        
        # Create multiple contexts
        contexts = []
        for i in range(3):
            context = Context(
                name=f'Test Context {i+1}',
                description=f'Context {i+1} for multi-context testing',
                source_type='files',
                status='ready',
                user_id=test_user.id
            )
            db.session.add(context)
            contexts.append(context)
        db.session.commit()
        
        context_ids = [ctx.id for ctx in contexts]
        
        with patch('services.vector_service.VectorService.search') as mock_search:
            # Mock search results from multiple contexts
            mock_search.return_value = [
                {
                    'content': f'Content from context {i+1}',
                    'metadata': {'source': f'context_{i+1}.txt'},
                    'score': 0.8 - (i * 0.1)
                }
                for i in range(3)
            ]
            
            with patch('services.llm_service.LLMService.generate_response') as mock_llm:
                mock_llm.return_value = {
                    'content': 'Response synthesized from multiple contexts.',
                    'citations': [
                        {
                            'source': f'context_{i+1}.txt',
                            'content': f'Content from context {i+1}',
                            'score': 0.8 - (i * 0.1)
                        }
                        for i in range(3)
                    ]
                }
                
                # Create session
                response = client.post('/api/chat/sessions', headers=auth_headers)
                session_data = json.loads(response.data)
                session_id = session_data['session']['id']
                
                # Send message with multiple contexts
                message_data = {
                    'message': 'Compare information across all contexts.',
                    'context_ids': context_ids
                }
                
                response = client.post(f'/api/chat/{session_id}',
                                     data=json.dumps(message_data),
                                     headers=auth_headers)
                
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Verify citations from multiple contexts
                citations = data['message']['citations']
                assert len(citations) == 3
                
                citation_sources = [c['source'] for c in citations]
                for i in range(3):
                    assert f'context_{i+1}.txt' in citation_sources
    
    def test_conversation_context_switching(self, client, auth_headers, test_user):
        """Test switching contexts mid-conversation."""
        from app import db
        
        # Create two different contexts
        context1 = Context(
            name='Technical Context',
            source_type='files',
            status='ready',
            user_id=test_user.id
        )
        context2 = Context(
            name='Business Context',
            source_type='files',
            status='ready',
            user_id=test_user.id
        )
        db.session.add_all([context1, context2])
        db.session.commit()
        
        with patch('services.vector_service.VectorService.search') as mock_search:
            with patch('services.llm_service.LLMService.generate_response') as mock_llm:
                # Create session
                response = client.post('/api/chat/sessions', headers=auth_headers)
                session_data = json.loads(response.data)
                session_id = session_data['session']['id']
                
                # First message with technical context
                mock_search.return_value = [
                    {
                        'content': 'Technical documentation content',
                        'metadata': {'source': 'tech_doc.md'},
                        'score': 0.95
                    }
                ]
                mock_llm.return_value = {
                    'content': 'Technical response',
                    'citations': [{'source': 'tech_doc.md', 'content': 'Technical documentation content'}]
                }
                
                message1_data = {
                    'message': 'Explain the technical architecture.',
                    'context_ids': [context1.id]
                }
                
                response = client.post(f'/api/chat/{session_id}',
                                     data=json.dumps(message1_data),
                                     headers=auth_headers)
                assert response.status_code == 200
                
                # Switch to business context
                mock_search.return_value = [
                    {
                        'content': 'Business requirements document',
                        'metadata': {'source': 'business_req.pdf'},
                        'score': 0.92
                    }
                ]
                mock_llm.return_value = {
                    'content': 'Business-focused response',
                    'citations': [{'source': 'business_req.pdf', 'content': 'Business requirements document'}]
                }
                
                message2_data = {
                    'message': 'What are the business requirements?',
                    'context_ids': [context2.id]
                }
                
                response = client.post(f'/api/chat/{session_id}',
                                     data=json.dumps(message2_data),
                                     headers=auth_headers)
                assert response.status_code == 200
                
                # Verify conversation history shows context switching
                response = client.get(f'/api/chat/{session_id}/history',
                                    headers=auth_headers)
                history_data = json.loads(response.data)
                
                messages = history_data['messages']
                assert len(messages) == 4  # 2 user + 2 assistant
                
                # Verify different contexts were used
                assert messages[1]['context_ids'] == [context1.id]
                assert messages[3]['context_ids'] == [context2.id]


class TestChatModel:
    """Test chat-related model functionality."""
    
    def test_chat_session_model(self, test_user):
        """Test ChatSession model functionality."""
        from app import db
        
        session = ChatSession(
            title='Test Session Model',
            user_id=test_user.id
        )
        db.session.add(session)
        db.session.commit()
        
        # Test model attributes
        assert session.title == 'Test Session Model'
        assert session.user_id == test_user.id
        assert session.message_count == 0
        assert session.created_at is not None
        
        # Test to_dict method
        session_dict = session.to_dict()
        expected_keys = ['id', 'title', 'created_at', 'updated_at', 'message_count']
        for key in expected_keys:
            assert key in session_dict
    
    def test_message_model(self, test_chat_session):
        """Test Message model functionality."""
        from app import db
        
        message = Message(
            session_id=test_chat_session.id,
            role='user',
            content='Test message content',
            context_ids=[1, 2, 3]
        )
        db.session.add(message)
        db.session.commit()
        
        # Test model attributes
        assert message.role == 'user'
        assert message.content == 'Test message content'
        assert message.context_ids == [1, 2, 3]
        assert message.session_id == test_chat_session.id
        
        # Test to_dict method
        message_dict = message.to_dict()
        expected_keys = ['id', 'role', 'content', 'context_ids', 'citations', 'created_at']
        for key in expected_keys:
            assert key in message_dict
    
    def test_message_citations_handling(self, test_chat_session):
        """Test message citations storage and retrieval."""
        from app import db
        
        citations = [
            {
                'source': 'document1.pdf',
                'content': 'Relevant content from document 1',
                'score': 0.95,
                'page': 5
            },
            {
                'source': 'document2.txt',
                'content': 'Another relevant piece of information',
                'score': 0.87
            }
        ]
        
        message = Message(
            session_id=test_chat_session.id,
            role='assistant',
            content='AI response with citations',
            citations=citations
        )
        db.session.add(message)
        db.session.commit()
        
        # Retrieve and verify citations
        db.session.refresh(message)
        assert len(message.citations) == 2
        assert message.citations[0]['source'] == 'document1.pdf'
        assert message.citations[1]['score'] == 0.87
    
    def test_session_message_relationship(self, test_chat_session):
        """Test relationship between sessions and messages."""
        from app import db
        
        # Create multiple messages for the session
        messages = []
        for i in range(3):
            message = Message(
                session_id=test_chat_session.id,
                role='user' if i % 2 == 0 else 'assistant',
                content=f'Message {i+1} content'
            )
            messages.append(message)
            db.session.add(message)
        
        db.session.commit()
        
        # Test session.messages relationship
        db.session.refresh(test_chat_session)
        assert len(test_chat_session.messages) >= 3
        
        # Verify message ordering (should be by creation time)
        session_messages = sorted(test_chat_session.messages, key=lambda m: m.created_at)
        for i, msg in enumerate(session_messages[-3:]):  # Last 3 messages
            assert f'Message {i+1} content' in msg.content