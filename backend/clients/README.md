# RAG Chatbot API Client

Python client library for the RAG Chatbot PWA API.

## Installation

```bash
pip install ragchatbot-api-client
```

## Quick Start

```python
from ragchatbot_client import RagChatbotClient

# Initialize client
client = RagChatbotClient('http://localhost:5000/api')

# Authenticate
token = client.authenticate('username', 'password')

# Create a context
context = client.create_context(
    name='My Documents',
    source_type='files',
    description='Personal document collection'
)

# Upload files
client.upload_files(context.id, ['document1.pdf', 'document2.docx'])

# Create chat session
session = client.create_chat_session('Document Q&A')

# Send message
response = client.send_message(
    session.id,
    'What are the main topics in my documents?',
    context_ids=[context.id]
)

print(f"Response: {response.content}")
```

## Features

- **Authentication**: Login, register, and manage user sessions
- **Context Management**: Create, update, and delete RAG contexts
- **File Upload**: Upload documents for processing
- **Chat Interface**: Send messages and receive AI responses
- **Streaming Support**: Real-time streaming responses
- **Error Handling**: Comprehensive error handling and logging

## API Reference

### Authentication

```python
# Login
token = client.authenticate('username', 'password')

# Register new user
client.register('username', 'email@example.com', 'password')

# Get user profile
profile = client.get_user_profile()
```

### Context Management

```python
# Create context
context = client.create_context(
    name='My Context',
    source_type='files',  # 'files', 'repo', 'database'
    description='Context description'
)

# Get all contexts
contexts = client.get_contexts()

# Get specific context
context = client.get_context(context_id)

# Delete context
client.delete_context(context_id)
```

### File Upload

```python
# Upload files to context
result = client.upload_files(context_id, [
    'path/to/file1.pdf',
    'path/to/file2.docx'
])
```

### Chat

```python
# Create chat session
session = client.create_chat_session('Session Title')

# Get all sessions
sessions = client.get_chat_sessions()

# Send message
response = client.send_message(
    session_id=session.id,
    message='Your question here',
    context_ids=[context.id]
)

# Get chat history
messages = client.get_chat_messages(session.id)
```

## Configuration

The client can be configured with various options:

```python
client = RagChatbotClient(
    base_url='http://localhost:5000/api',
    token='your-jwt-token',  # Optional: set token directly
)

# Set token later
client.set_token('your-jwt-token')

# Remove authentication
client.logout()
```

## Error Handling

The client raises exceptions for various error conditions:

```python
try:
    context = client.create_context(name='Test', source_type='files')
except Exception as e:
    print(f"Error creating context: {e}")
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/your-org/ragchatbot-api-client
cd ragchatbot-api-client
pip install -e .[dev]
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black ragchatbot_client/
flake8 ragchatbot_client/
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.ragchatbot.com/api-client
- Issues: https://github.com/your-org/ragchatbot-api-client/issues
- Email: support@ragchatbot.com
