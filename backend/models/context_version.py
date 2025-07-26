"""
Context versioning system for tracking changes and updates
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models import db
import json

class ContextVersion(db.Model):
    """Model for tracking context versions"""
    __tablename__ = 'context_versions'
    
    id = Column(Integer, primary_key=True)
    context_id = Column(Integer, ForeignKey('contexts.id'), nullable=False)
    version_number = Column(String(20), nullable=False)  # e.g., "1.0", "1.1", "2.0"
    description = Column(Text)
    
    # Configuration snapshot
    config_snapshot = Column(Text)  # JSON string of config at this version
    chunk_strategy = Column(String(50))
    embedding_model = Column(String(100))
    
    # Statistics
    total_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_documents = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default='active')  # 'active', 'archived', 'deprecated'
    is_current = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Change tracking
    changes_summary = Column(Text)  # JSON string describing what changed
    parent_version_id = Column(Integer, ForeignKey('context_versions.id'))
    
    # Relationships
    context = relationship('Context', backref='versions')
    created_by_user = relationship('User')
    parent_version = relationship('ContextVersion', remote_side=[id])
    
    def get_config_snapshot(self):
        """Get configuration snapshot as dict"""
        return json.loads(self.config_snapshot) if self.config_snapshot else {}
    
    def set_config_snapshot(self, config_dict):
        """Set configuration snapshot from dict"""
        self.config_snapshot = json.dumps(config_dict)
    
    def get_changes_summary(self):
        """Get changes summary as dict"""
        return json.loads(self.changes_summary) if self.changes_summary else {}
    
    def set_changes_summary(self, changes_dict):
        """Set changes summary from dict"""
        self.changes_summary = json.dumps(changes_dict)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'context_id': self.context_id,
            'version_number': self.version_number,
            'description': self.description,
            'config_snapshot': self.get_config_snapshot(),
            'chunk_strategy': self.chunk_strategy,
            'embedding_model': self.embedding_model,
            'total_chunks': self.total_chunks,
            'total_tokens': self.total_tokens,
            'total_documents': self.total_documents,
            'status': self.status,
            'is_current': self.is_current,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'changes_summary': self.get_changes_summary(),
            'parent_version_id': self.parent_version_id
        }

class ContextVersionService:
    """Service for managing context versions"""
    
    @staticmethod
    def create_version(context, user_id, description=None, changes=None):
        """Create a new version of a context"""
        
        # Get the latest version number
        latest_version = ContextVersion.query.filter_by(
            context_id=context.id
        ).order_by(ContextVersion.version_number.desc()).first()
        
        if latest_version:
            # Increment version number
            major, minor = map(int, latest_version.version_number.split('.'))
            new_version_number = f"{major}.{minor + 1}"
        else:
            new_version_number = "1.0"
        
        # Mark all previous versions as not current
        ContextVersion.query.filter_by(
            context_id=context.id,
            is_current=True
        ).update({'is_current': False})
        
        # Create new version
        version = ContextVersion(
            context_id=context.id,
            version_number=new_version_number,
            description=description or f"Version {new_version_number}",
            chunk_strategy=context.chunk_strategy,
            embedding_model=context.embedding_model,
            total_chunks=context.total_chunks,
            total_tokens=context.total_tokens,
            status='active',
            is_current=True,
            created_by=user_id,
            parent_version_id=latest_version.id if latest_version else None
        )
        
        # Set configuration snapshot
        version.set_config_snapshot(context.get_config())
        
        # Set changes summary
        if changes:
            version.set_changes_summary(changes)
        
        db.session.add(version)
        db.session.commit()
        
        return version
    
    @staticmethod
    def get_version_history(context_id):
        """Get version history for a context"""
        return ContextVersion.query.filter_by(
            context_id=context_id
        ).order_by(ContextVersion.created_at.desc()).all()
    
    @staticmethod
    def get_current_version(context_id):
        """Get the current version of a context"""
        return ContextVersion.query.filter_by(
            context_id=context_id,
            is_current=True
        ).first()
    
    @staticmethod
    def restore_version(context_id, version_id, user_id):
        """Restore a context to a specific version"""
        
        # Get the version to restore
        from models import db
        version_to_restore = db.session.get(ContextVersion, version_id)
        if not version_to_restore or version_to_restore.context_id != context_id:
            raise ValueError("Version not found")

        # Get the context
        from models import Context
        context = db.session.get(Context, context_id)
        if not context:
            raise ValueError("Context not found")
        
        # Update context with version configuration
        config_snapshot = version_to_restore.get_config_snapshot()
        context.set_config(config_snapshot)
        context.chunk_strategy = version_to_restore.chunk_strategy
        context.embedding_model = version_to_restore.embedding_model
        
        # Create a new version for this restoration
        changes = {
            'type': 'restoration',
            'restored_from_version': version_to_restore.version_number,
            'restored_at': datetime.utcnow().isoformat()
        }
        
        new_version = ContextVersionService.create_version(
            context=context,
            user_id=user_id,
            description=f"Restored from version {version_to_restore.version_number}",
            changes=changes
        )
        
        db.session.commit()
        
        return new_version
    
    @staticmethod
    def compare_versions(version1_id, version2_id):
        """Compare two versions and return differences"""
        
        from models import db
        version1 = db.session.get(ContextVersion, version1_id)
        version2 = db.session.get(ContextVersion, version2_id)
        
        if not version1 or not version2:
            raise ValueError("One or both versions not found")
        
        config1 = version1.get_config_snapshot()
        config2 = version2.get_config_snapshot()
        
        differences = {
            'version_numbers': {
                'from': version1.version_number,
                'to': version2.version_number
            },
            'chunk_strategy': {
                'from': version1.chunk_strategy,
                'to': version2.chunk_strategy,
                'changed': version1.chunk_strategy != version2.chunk_strategy
            },
            'embedding_model': {
                'from': version1.embedding_model,
                'to': version2.embedding_model,
                'changed': version1.embedding_model != version2.embedding_model
            },
            'statistics': {
                'chunks': {
                    'from': version1.total_chunks,
                    'to': version2.total_chunks,
                    'change': version2.total_chunks - version1.total_chunks
                },
                'tokens': {
                    'from': version1.total_tokens,
                    'to': version2.total_tokens,
                    'change': version2.total_tokens - version1.total_tokens
                }
            },
            'config_changes': ContextVersionService._compare_configs(config1, config2)
        }
        
        return differences
    
    @staticmethod
    def _compare_configs(config1, config2):
        """Compare two configuration dictionaries"""
        changes = {}
        
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 != val2:
                changes[key] = {
                    'from': val1,
                    'to': val2,
                    'type': 'modified' if key in config1 and key in config2 else 
                           'added' if key not in config1 else 'removed'
                }
        
        return changes
