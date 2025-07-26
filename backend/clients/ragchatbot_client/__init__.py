"""
RAG Chatbot API Client Library

A Python client library for interacting with the RAG Chatbot PWA API.
"""

from .python_client import (
    RagChatbotClient,
    Context,
    ChatMessage,
    ChatSession
)

__version__ = "1.0.0"
__author__ = "RAG Chatbot Team"
__email__ = "support@ragchatbot.com"

__all__ = [
    "RagChatbotClient",
    "Context", 
    "ChatMessage",
    "ChatSession"
]
