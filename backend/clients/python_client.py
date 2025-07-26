"""
Python API Client for RAG Chatbot PWA
"""

import requests
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Context:
    """Context data class"""
    id: int
    name: str
    source_type: str
    status: str
    total_chunks: int = 0
    total_tokens: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ChatMessage:
    """Chat message data class"""
    id: int
    role: str
    content: str
    session_id: int
    created_at: Optional[str] = None
    context_ids: Optional[List[int]] = None
    citations: Optional[List[Dict]] = None


@dataclass
class ChatSession:
    """Chat session data class"""
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str
    message_count: int = 0


class RagChatbotClient:
    """Python client for RAG Chatbot API"""
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API (e.g., 'http://localhost:5000/api')
            token: JWT authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def authenticate(self, username: str, password: str) -> str:
        """
        Authenticate and get JWT token
        
        Args:
            username: Username
            password: Password
            
        Returns:
            JWT token string
        """
        data = {
            'username': username,
            'password': password
        }
        
        response = self._request('POST', '/auth/login', json=data)
        token = response.get('access_token')
        
        if token:
            self.token = token
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
        
        return token
    
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register new user
        
        Args:
            username: Username
            email: Email address
            password: Password
            
        Returns:
            User registration response
        """
        data = {
            'username': username,
            'email': email,
            'password': password
        }
        
        return self._request('POST', '/auth/register', json=data)
    
    # Context methods
    def create_context(self, name: str, source_type: str, **kwargs) -> Context:
        """
        Create a new context
        
        Args:
            name: Context name
            source_type: Type of source ('files', 'repo', 'database')
            **kwargs: Additional context configuration
            
        Returns:
            Created context
        """
        data = {
            'name': name,
            'source_type': source_type,
            **kwargs
        }
        
        response = self._request('POST', '/contexts', json=data)
        return Context(**response)
    
    def get_contexts(self) -> List[Context]:
        """
        Get all user contexts
        
        Returns:
            List of contexts
        """
        response = self._request('GET', '/contexts')
        return [Context(**ctx) for ctx in response]
    
    def get_context(self, context_id: int) -> Context:
        """
        Get specific context
        
        Args:
            context_id: Context ID
            
        Returns:
            Context details
        """
        response = self._request('GET', f'/contexts/{context_id}')
        return Context(**response)
    
    def delete_context(self, context_id: int) -> Dict[str, Any]:
        """
        Delete a context
        
        Args:
            context_id: Context ID
            
        Returns:
            Deletion response with cleanup stats
        """
        return self._request('DELETE', f'/contexts/{context_id}')
    
    def upload_files(self, context_id: int, files: List[str]) -> Dict[str, Any]:
        """
        Upload files to a context
        
        Args:
            context_id: Context ID
            files: List of file paths to upload
            
        Returns:
            Upload response
        """
        files_data = []
        for file_path in files:
            with open(file_path, 'rb') as f:
                files_data.append(('files', f))
        
        # Remove Content-Type header for multipart upload
        headers = self.session.headers.copy()
        if 'Content-Type' in headers:
            del headers['Content-Type']
        
        return self._request(
            'POST', 
            f'/upload/{context_id}', 
            files=files_data,
            headers=headers
        )
    
    # Chat methods
    def create_chat_session(self, title: Optional[str] = None) -> ChatSession:
        """
        Create a new chat session
        
        Args:
            title: Optional session title
            
        Returns:
            Created chat session
        """
        data = {}
        if title:
            data['title'] = title
        
        response = self._request('POST', '/chat/sessions', json=data)
        return ChatSession(**response)
    
    def get_chat_sessions(self) -> List[ChatSession]:
        """
        Get all chat sessions
        
        Returns:
            List of chat sessions
        """
        response = self._request('GET', '/chat/sessions')
        return [ChatSession(**session) for session in response]
    
    def get_chat_session(self, session_id: int) -> ChatSession:
        """
        Get specific chat session
        
        Args:
            session_id: Session ID
            
        Returns:
            Chat session details
        """
        response = self._request('GET', f'/chat/sessions/{session_id}')
        return ChatSession(**response)
    
    def send_message(self, session_id: int, message: str, 
                    context_ids: Optional[List[int]] = None,
                    stream: bool = False) -> Union[ChatMessage, Dict[str, Any]]:
        """
        Send a chat message
        
        Args:
            session_id: Chat session ID
            message: Message content
            context_ids: List of context IDs to use for RAG
            stream: Whether to use streaming response
            
        Returns:
            Chat response or streaming response info
        """
        data = {
            'session_id': session_id,
            'message': message,
            'stream': stream
        }
        
        if context_ids:
            data['context_ids'] = context_ids
        
        response = self._request('POST', '/chat/query', json=data)
        
        if stream:
            return response  # Streaming response info
        else:
            return ChatMessage(**response.get('assistant_message', {}))
    
    def get_chat_messages(self, session_id: int) -> List[ChatMessage]:
        """
        Get messages for a chat session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of chat messages
        """
        response = self._request('GET', f'/chat/sessions/{session_id}/messages')
        return [ChatMessage(**msg) for msg in response]
    
    # Utility methods
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health
        
        Returns:
            Health status
        """
        return self._request('GET', '/health')
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get current user profile
        
        Returns:
            User profile data
        """
        return self._request('GET', '/auth/profile')


# Example usage
if __name__ == '__main__':
    # Initialize client
    client = RagChatbotClient('http://localhost:5000/api')
    
    # Authenticate
    token = client.authenticate('username', 'password')
    print(f"Authenticated with token: {token[:20]}...")
    
    # Create context
    context = client.create_context(
        name='My Documents',
        source_type='files',
        description='Personal document collection'
    )
    print(f"Created context: {context.name} (ID: {context.id})")
    
    # Upload files (example)
    # client.upload_files(context.id, ['document1.pdf', 'document2.docx'])
    
    # Create chat session
    session = client.create_chat_session('Document Q&A')
    print(f"Created session: {session.title} (ID: {session.id})")
    
    # Send message
    response = client.send_message(
        session.id,
        'What are the main topics in my documents?',
        context_ids=[context.id]
    )
    print(f"Response: {response.content}")
