"""
User Preferences Model for RAG Chatbot

This module defines the database model for storing user preferences and settings.
Supports hierarchical settings organization, type validation, and change tracking.

Features:
- Hierarchical preference organization (categories/sections)
- Type-safe preference storage with validation
- Change tracking and audit trail
- Default value management
- JSON schema validation for complex preferences
- Preference sharing and inheritance
- Performance optimized queries

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, CheckConstraint

from database import db
# Define TimestampMixin locally to avoid import issues
from datetime import datetime
from sqlalchemy import Column, DateTime

class TimestampMixin:
    """
    Mixin class to add timestamp fields to models
    
    Provides created_at and updated_at fields with automatic timestamp management.
    """
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

logger = logging.getLogger(__name__)

# Preference categories and their schemas
PREFERENCE_SCHEMAS = {
    'appearance': {
        'type': 'object',
        'properties': {
            'theme': {'type': 'string', 'enum': ['light', 'dark', 'system']},
            'fontSize': {'type': 'string', 'enum': ['small', 'medium', 'large']},
            'fontFamily': {'type': 'string'},
            'compactMode': {'type': 'boolean'},
            'language': {'type': 'string'},
            'timezone': {'type': 'string'},
        },
        'additionalProperties': False
    },
    'chat': {
        'type': 'object',
        'properties': {
            'defaultModel': {'type': 'string'},
            'messageLimit': {'type': 'integer', 'minimum': 10, 'maximum': 1000},
            'autoSave': {'type': 'boolean'},
            'showTimestamps': {'type': 'boolean'},
            'enableNotifications': {'type': 'boolean'},
            'soundEffects': {'type': 'boolean'},
            'typingIndicator': {'type': 'boolean'},
        },
        'additionalProperties': False
    },
    'search': {
        'type': 'object',
        'properties': {
            'defaultSearchType': {'type': 'string', 'enum': ['semantic', 'keyword', 'hybrid']},
            'maxResults': {'type': 'integer', 'minimum': 5, 'maximum': 100},
            'enableAutoComplete': {'type': 'boolean'},
            'searchHistory': {'type': 'boolean'},
            'indexingEnabled': {'type': 'boolean'},
        },
        'additionalProperties': False
    },
    'privacy': {
        'type': 'object',
        'properties': {
            'shareUsageData': {'type': 'boolean'},
            'enableAnalytics': {'type': 'boolean'},
            'dataRetentionDays': {'type': 'integer', 'minimum': 7, 'maximum': 365},
            'exportFormat': {'type': 'string', 'enum': ['json', 'csv', 'markdown']},
        },
        'additionalProperties': False
    },
    'performance': {
        'type': 'object',
        'properties': {
            'cacheSize': {'type': 'integer', 'minimum': 10, 'maximum': 1000},
            'prefetchEnabled': {'type': 'boolean'},
            'compressionLevel': {'type': 'integer', 'minimum': 0, 'maximum': 9},
            'batchSize': {'type': 'integer', 'minimum': 1, 'maximum': 100},
        },
        'additionalProperties': False
    }
}

# Default preferences
DEFAULT_PREFERENCES = {
    'appearance': {
        'theme': 'system',
        'fontSize': 'medium',
        'fontFamily': 'system',
        'compactMode': False,
        'language': 'en',
        'timezone': 'UTC',
    },
    'chat': {
        'defaultModel': 'gemini-pro',
        'messageLimit': 100,
        'autoSave': True,
        'showTimestamps': True,
        'enableNotifications': True,
        'soundEffects': False,
        'typingIndicator': True,
    },
    'search': {
        'defaultSearchType': 'hybrid',
        'maxResults': 20,
        'enableAutoComplete': True,
        'searchHistory': True,
        'indexingEnabled': True,
    },
    'privacy': {
        'shareUsageData': False,
        'enableAnalytics': False,
        'dataRetentionDays': 90,
        'exportFormat': 'json',
    },
    'performance': {
        'cacheSize': 100,
        'prefetchEnabled': True,
        'compressionLevel': 6,
        'batchSize': 10,
    }
}


# UserPreferences class is now defined in models.py to avoid table redefinition


class PreferenceTemplate(db.Model, TimestampMixin):
    """
    Preference Templates for sharing common preference sets.
    """
    __tablename__ = 'preference_templates'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Template information
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)
    
    # Template data
    preferences = db.Column(db.JSON, nullable=False)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    version = db.Column(db.String(10), default='1.0')
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref=db.backref('preference_templates', lazy='dynamic'))
    
    # Constraints
    __table_args__ = (
        Index('ix_preference_templates_category_public', 'category', 'is_public'),
        Index('ix_preference_templates_creator_public', 'created_by', 'is_public'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'preferences': self.preferences,
            'created_by': self.created_by,
            'is_system': self.is_system,
            'is_public': self.is_public,
            'version': self.version,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def apply_to_user(self, user_id: int) -> int:
        """
        Apply this template's preferences to a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of preferences applied
        """
        try:
            count = 0
            for key, value in self.preferences.items():
                UserPreferences.set_user_preference(
                    user_id=user_id,
                    category=self.category,
                    key=key,
                    value=value,
                    description=f"Applied from template: {self.name}"
                )
                count += 1
            
            # Increment usage count
            self.usage_count += 1
            db.session.commit()
            
            logger.info(f"Applied template {self.name} to user {user_id}: {count} preferences")
            return count
            
        except Exception as e:
            logger.error(f"Failed to apply template {self.name} to user {user_id}: {e}")
            db.session.rollback()
            raise
    
    def __repr__(self) -> str:
        """String representation of the template."""
        return f"<PreferenceTemplate {self.name} ({self.category})>"