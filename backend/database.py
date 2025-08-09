"""
Database initialization module for RAG Chatbot PWA

This module provides the central database instance to avoid circular imports
between models and their extensions.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize the central database instance
db = SQLAlchemy()

def init_app(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    return db