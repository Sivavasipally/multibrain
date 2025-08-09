"""
Enhanced Context Versioning Models for RAG Chatbot PWA

This module provides a comprehensive context versioning system that tracks changes to 
knowledge bases, enables version comparison, rollback functionality, and audit trails.
It builds upon the existing basic versioning with advanced features.

Key Enhancements:
- Comprehensive snapshot preservation with integrity checks
- Automatic and manual versioning triggers
- Version tagging and categorization
- Advanced diff tracking and comparison
- Rollback and restore capabilities with safety checks
- Performance metrics per version
- Audit trails and change history

Architecture:
- ContextVersion: Enhanced version snapshots with full state preservation
- ContextVersionDiff: Detailed change tracking between versions
- VersionTag: Named tags for important versions
- ContextVersionService: Business logic for version management

Author: RAG Chatbot Development Team
Version: 2.0.0 (Enhanced)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from database import db
import json
import hashlib
from typing import Dict, Any, Optional, List

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('context_version')

class ContextVersion(db.Model):
    """
    Enhanced context version model with comprehensive state tracking
    
    Stores complete snapshots of context states including configuration, documents,
    processing metrics, and metadata. Provides integrity checking and comparison
    capabilities for robust version management.
    
    Key Features:
    - Complete state snapshot preservation
    - SHA-256 integrity verification
    - Automatic and manual version creation
    - Version comparison and rollback
    - Performance metrics tracking
    - Comprehensive audit trails
    
    Version Types:
    - auto: Automatic system-triggered versions
    - manual: User-created versions
    - milestone: Important milestone versions
    - backup: Safety backup versions
    - rollback: Created during rollback operations
    
    Example:
        >>> version = ContextVersionService.create_version(
        ...     context, user_id, "Added documentation files", version_type='manual'
        ... )
        >>> print(f"Created version {version.version_number} with hash {version.content_hash[:8]}")
    """
    __tablename__ = 'context_versions'
    
    # Primary identification
    id = Column(Integer, primary_key=True, doc="Unique version identifier")
    context_id = Column(Integer, ForeignKey('contexts.id'), nullable=False, doc="Parent context reference")
    
    # Version identification and metadata
    version_number = Column(String(20), nullable=False, doc="Semantic version number (e.g., 1.0, 1.1, 2.0)")
    version_type = Column(String(20), default='auto', doc="Version type: auto, manual, milestone, backup, rollback")
    content_hash = Column(String(64), nullable=False, doc="SHA-256 hash of version content for integrity")
    description = Column(Text, doc="Description of changes in this version")
    
    # Complete state snapshot - stores full context state
    config_snapshot = Column(Text, doc="JSON snapshot of context configuration")
    documents_snapshot = Column(Text, doc="JSON snapshot of documents metadata")
    processing_snapshot = Column(Text, doc="JSON snapshot of processing state and metrics")
    
    # Version-specific configuration
    chunk_strategy = Column(String(50), doc="Chunking strategy used in this version")
    embedding_model = Column(String(100), doc="Embedding model used in this version")
    
    # Content statistics at version time
    total_chunks = Column(Integer, default=0, doc="Number of text chunks in this version")
    total_tokens = Column(Integer, default=0, doc="Total tokens processed in this version") 
    total_documents = Column(Integer, default=0, doc="Number of documents in this version")
    vector_store_size = Column(Integer, default=0, doc="Size of vector store in bytes")
    
    # Processing performance metrics
    processing_duration = Column(Integer, doc="Processing time in seconds")
    avg_chunk_size = Column(Integer, doc="Average chunk size in characters")
    embedding_dimensions = Column(Integer, doc="Embedding vector dimensions")
    
    # Version status and lifecycle
    status = Column(String(50), default='active', doc="Version status: active, archived, deprecated, corrupted")
    is_current = Column(Boolean, default=False, doc="Whether this is the active version")
    is_protected = Column(Boolean, default=False, doc="Whether version is protected from deletion")
    
    # Audit and tracking
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, doc="User who created this version")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), doc="Version creation timestamp")
    parent_version_id = Column(Integer, ForeignKey('context_versions.id'), doc="Previous version ID")
    
    # Change tracking
    changes_summary = Column(Text, doc="JSON summary of changes made in this version")
    change_impact = Column(String(20), default='minor', doc="Impact level: minor, major, breaking")
    
    # Relationships - defined after class definitions to avoid circular imports
    context = relationship('Context', backref=db.backref('versions', cascade='all, delete-orphan'))
    created_by_user = relationship('User', backref='created_versions')
    parent_version = relationship('ContextVersion', remote_side=[id], backref='child_versions')
    
    # Database constraints and indexes
    __table_args__ = (
        UniqueConstraint('context_id', 'version_number', name='unique_context_version'),
        Index('idx_context_versions_context_created', 'context_id', 'created_at'),
        Index('idx_context_versions_current', 'context_id', 'is_current'),
        Index('idx_context_versions_hash', 'content_hash'),
    )
    
    def get_config_snapshot(self) -> Dict[str, Any]:
        """
        Get configuration snapshot as dictionary
        
        Returns:
            Dict[str, Any]: Parsed configuration snapshot
        """
        return json.loads(self.config_snapshot) if self.config_snapshot else {}
    
    def set_config_snapshot(self, config_dict: Dict[str, Any]):
        """
        Set configuration snapshot from dictionary
        
        Args:
            config_dict: Configuration dictionary to store
        """
        self.config_snapshot = json.dumps(config_dict, sort_keys=True)
    
    def get_documents_snapshot(self) -> List[Dict[str, Any]]:
        """
        Get documents snapshot as list
        
        Returns:
            List[Dict[str, Any]]: List of document metadata snapshots
        """
        return json.loads(self.documents_snapshot) if self.documents_snapshot else []
    
    def set_documents_snapshot(self, documents_list: List[Dict[str, Any]]):
        """
        Set documents snapshot from list
        
        Args:
            documents_list: List of document metadata to store
        """
        self.documents_snapshot = json.dumps(documents_list, sort_keys=True)
    
    def get_processing_snapshot(self) -> Dict[str, Any]:
        """
        Get processing snapshot as dictionary
        
        Returns:
            Dict[str, Any]: Processing state and metrics
        """
        return json.loads(self.processing_snapshot) if self.processing_snapshot else {}
    
    def set_processing_snapshot(self, processing_dict: Dict[str, Any]):
        """
        Set processing snapshot from dictionary
        
        Args:
            processing_dict: Processing state dictionary to store
        """
        self.processing_snapshot = json.dumps(processing_dict, sort_keys=True)
    
    def get_changes_summary(self) -> Dict[str, Any]:
        """
        Get changes summary as dictionary
        
        Returns:
            Dict[str, Any]: Summary of changes in this version
        """
        return json.loads(self.changes_summary) if self.changes_summary else {}
    
    def set_changes_summary(self, changes_dict: Dict[str, Any]):
        """
        Set changes summary from dictionary
        
        Args:
            changes_dict: Changes summary dictionary to store
        """
        self.changes_summary = json.dumps(changes_dict, sort_keys=True)
    
    def calculate_content_hash(self) -> str:
        """
        Calculate SHA-256 hash of version content for integrity verification
        
        Returns:
            str: SHA-256 hash of version content
        """
        content_data = {
            'config': self.get_config_snapshot(),
            'documents': self.get_documents_snapshot(),
            'processing': self.get_processing_snapshot(),
            'metadata': {
                'chunk_strategy': self.chunk_strategy,
                'embedding_model': self.embedding_model,
                'total_chunks': self.total_chunks,
                'total_tokens': self.total_tokens,
                'total_documents': self.total_documents
            }
        }
        
        content_json = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """
        Verify version integrity by comparing stored hash with calculated hash
        
        Returns:
            bool: True if integrity is intact, False otherwise
        """
        try:
            calculated_hash = self.calculate_content_hash()
            return calculated_hash == self.content_hash
        except Exception as e:
            logger.error(f"Error verifying integrity for version {self.id}: {e}")
            return False
    
    def to_dict(self, include_snapshots: bool = False) -> Dict[str, Any]:
        """
        Convert version to dictionary representation
        
        Args:
            include_snapshots: Whether to include full snapshot data
            
        Returns:
            Dict[str, Any]: Version data for API responses
        """
        data = {
            'id': self.id,
            'context_id': self.context_id,
            'version_number': self.version_number,
            'version_type': self.version_type,
            'content_hash': self.content_hash,
            'description': self.description,
            'chunk_strategy': self.chunk_strategy,
            'embedding_model': self.embedding_model,
            'total_chunks': self.total_chunks,
            'total_tokens': self.total_tokens,
            'total_documents': self.total_documents,
            'vector_store_size': self.vector_store_size,
            'processing_duration': self.processing_duration,
            'avg_chunk_size': self.avg_chunk_size,
            'embedding_dimensions': self.embedding_dimensions,
            'status': self.status,
            'is_current': self.is_current,
            'is_protected': self.is_protected,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'parent_version_id': self.parent_version_id,
            'changes_summary': self.get_changes_summary(),
            'change_impact': self.change_impact,
            'integrity_verified': self.verify_integrity(),
            'tags': [tag.to_dict() for tag in self.version_tags]
        }
        
        if include_snapshots:
            data.update({
                'config_snapshot': self.get_config_snapshot(),
                'documents_snapshot': self.get_documents_snapshot(),
                'processing_snapshot': self.get_processing_snapshot()
            })
        
        return data

class ContextVersionDiff(db.Model):
    """
    Detailed difference tracking between context versions
    
    Records specific changes between versions for audit trails and
    detailed change analysis.
    """
    __tablename__ = 'context_version_diffs'
    
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('context_versions.id'), nullable=False)
    previous_version_id = Column(Integer, ForeignKey('context_versions.id'), nullable=True)
    
    # Change classification
    change_type = Column(String(50), nullable=False)  # config, document, processing, metadata
    change_operation = Column(String(20), nullable=False)  # added, removed, modified
    change_description = Column(Text)
    
    # Change details
    change_data = Column(Text)  # JSON data with specific change information
    impact_score = Column(Integer, default=1)  # 1-10 scale of change impact
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_change_data(self) -> Dict[str, Any]:
        """Get change data as dictionary"""
        return json.loads(self.change_data) if self.change_data else {}
    
    def set_change_data(self, data_dict: Dict[str, Any]):
        """Set change data from dictionary"""
        self.change_data = json.dumps(data_dict, sort_keys=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert diff to dictionary representation"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'previous_version_id': self.previous_version_id,
            'change_type': self.change_type,
            'change_operation': self.change_operation,
            'change_description': self.change_description,
            'change_data': self.get_change_data(),
            'impact_score': self.impact_score,
            'created_at': self.created_at.isoformat()
        }

class VersionTag(db.Model):
    """
    Version tagging system for named and categorized versions
    
    Allows users and system to tag important versions with meaningful names
    and categories for easy reference and management.
    """
    __tablename__ = 'version_tags'
    
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('context_versions.id'), nullable=False)
    
    tag_name = Column(String(100), nullable=False)
    tag_description = Column(Text)
    tag_type = Column(String(50), default='user')  # user, system, milestone, release, backup
    tag_color = Column(String(7), default='#007bff')  # Hex color for UI display
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('version_id', 'tag_name', name='unique_version_tag'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary representation"""
        return {
            'id': self.id,
            'tag_name': self.tag_name,
            'tag_description': self.tag_description,
            'tag_type': self.tag_type,
            'tag_color': self.tag_color,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

# Define complex relationships after all models are defined to avoid foreign key ambiguity
ContextVersion.version_diffs = relationship(
    'ContextVersionDiff', 
    primaryjoin='ContextVersion.id == ContextVersionDiff.version_id',
    backref='version', 
    cascade='all, delete-orphan'
)

ContextVersion.version_tags = relationship(
    'VersionTag', 
    backref='version', 
    cascade='all, delete-orphan'
)

# Keep existing service for backward compatibility, but enhance it
class ContextVersionService:
    """
    Enhanced service for comprehensive context version management
    
    Provides business logic for creating, managing, comparing, and restoring
    context versions with advanced features like automatic versioning,
    integrity checking, and rollback safety.
    """
    
    @staticmethod
    def create_version(context, user_id: int = None, description: str = None, 
                      version_type: str = 'auto', changes: Dict[str, Any] = None,
                      force_major: bool = False) -> ContextVersion:
        """
        Create a new enhanced version of a context with comprehensive state capture
        
        Args:
            context: Context object to version
            user_id: ID of user creating version (None for system)
            description: Description of changes
            version_type: Type of version (auto, manual, milestone, backup, rollback)
            changes: Dictionary of changes made
            force_major: Whether to force a major version increment
            
        Returns:
            ContextVersion: Newly created version with full state snapshot
        """
        logger.info(f"Creating new version for context {context.id} by user {user_id}")
        
        try:
            # Get latest version for numbering
            latest_version = ContextVersion.query.filter_by(
                context_id=context.id
            ).order_by(ContextVersion.version_number.desc()).first()
            
            # Calculate new version number
            new_version_number = ContextVersionService._calculate_version_number(
                latest_version, force_major, changes
            )
            
            # Create comprehensive snapshots
            config_snapshot = context.get_config()
            documents_snapshot = [doc.to_dict() for doc in context.documents]
            processing_snapshot = {
                'status': context.status,
                'progress': context.progress,
                'error_message': context.error_message,
                'vector_store_path': context.vector_store_path,
                'updated_at': context.updated_at.isoformat() if context.updated_at else None
            }
            
            # Mark previous versions as not current
            ContextVersion.query.filter_by(
                context_id=context.id, is_current=True
            ).update({'is_current': False})
            
            # Create new version with full state
            version = ContextVersion(
                context_id=context.id,
                version_number=new_version_number,
                version_type=version_type,
                description=description or f"Version {new_version_number}",
                chunk_strategy=context.chunk_strategy,
                embedding_model=context.embedding_model,
                total_chunks=context.total_chunks or 0,
                total_tokens=context.total_tokens or 0,
                total_documents=len(context.documents),
                status='active',
                is_current=True,
                created_by=user_id,
                parent_version_id=latest_version.id if latest_version else None,
                change_impact=ContextVersionService._calculate_change_impact(changes)
            )
            
            # Set snapshots
            version.set_config_snapshot(config_snapshot)
            version.set_documents_snapshot(documents_snapshot)
            version.set_processing_snapshot(processing_snapshot)
            
            if changes:
                version.set_changes_summary(changes)
            
            # Calculate and set content hash for integrity
            version.content_hash = version.calculate_content_hash()
            
            # Add to session and commit
            db.session.add(version)
            db.session.commit()
            
            # Create diff record if there's a previous version
            if latest_version:
                ContextVersionService._create_version_diffs(latest_version, version, changes)
            
            logger.info(f"Successfully created version {new_version_number} for context {context.id}")
            return version
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create version for context {context.id}: {e}")
            log_error_with_context(e, {
                "context_id": context.id,
                "user_id": user_id,
                "version_type": version_type,
                "operation": "create_version"
            })
            raise
    
    @staticmethod
    def _calculate_version_number(latest_version: Optional[ContextVersion], 
                                force_major: bool, changes: Optional[Dict[str, Any]]) -> str:
        """Calculate new version number based on changes and previous version"""
        if not latest_version:
            return "1.0"
        
        try:
            major, minor = map(int, latest_version.version_number.split('.'))
        except ValueError:
            # Fallback for invalid version numbers
            return "1.0"
        
        # Determine if this should be a major or minor version increment
        if force_major or ContextVersionService._is_major_change(changes):
            return f"{major + 1}.0"
        else:
            return f"{major}.{minor + 1}"
    
    @staticmethod
    def _is_major_change(changes: Optional[Dict[str, Any]]) -> bool:
        """Determine if changes constitute a major version increment"""
        if not changes:
            return False
        
        major_change_indicators = [
            'config_change', 'embedding_model_change', 'chunk_strategy_change',
            'large_document_addition', 'document_removal'
        ]
        
        return any(indicator in changes for indicator in major_change_indicators)
    
    @staticmethod
    def _calculate_change_impact(changes: Optional[Dict[str, Any]]) -> str:
        """Calculate impact level of changes"""
        if not changes:
            return 'minor'
        
        # Analyze changes to determine impact
        major_indicators = ['config_change', 'embedding_model_change']
        breaking_indicators = ['chunk_strategy_change', 'major_document_removal']
        
        if any(indicator in changes for indicator in breaking_indicators):
            return 'breaking'
        elif any(indicator in changes for indicator in major_indicators):
            return 'major'
        else:
            return 'minor'
    
    @staticmethod
    def _create_version_diffs(previous_version: ContextVersion, new_version: ContextVersion,
                            changes: Optional[Dict[str, Any]]):
        """Create detailed diff records between versions"""
        try:
            if not changes:
                return
            
            for change_type, change_details in changes.items():
                if isinstance(change_details, dict):
                    diff = ContextVersionDiff(
                        version_id=new_version.id,
                        previous_version_id=previous_version.id,
                        change_type=change_type,
                        change_operation=change_details.get('operation', 'modified'),
                        change_description=change_details.get('description', f"{change_type} changed"),
                        impact_score=change_details.get('impact_score', 1)
                    )
                    diff.set_change_data(change_details)
                    db.session.add(diff)
            
            db.session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to create version diffs: {e}")
            # Don't fail the whole version creation for diff issues
    
    @staticmethod
    def get_version_history(context_id: int, limit: int = 50) -> List[ContextVersion]:
        """
        Get comprehensive version history for a context
        
        Args:
            context_id: Context ID to get history for
            limit: Maximum number of versions to return
            
        Returns:
            List[ContextVersion]: Ordered list of versions (newest first)
        """
        return ContextVersion.query.filter_by(
            context_id=context_id
        ).order_by(ContextVersion.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_current_version(context_id: int) -> Optional[ContextVersion]:
        """Get the current active version of a context"""
        return ContextVersion.query.filter_by(
            context_id=context_id, is_current=True
        ).first()
    
    @staticmethod
    def restore_version(context_id: int, version_id: int, user_id: int) -> ContextVersion:
        """
        Restore a context to a specific version with safety checks
        
        Args:
            context_id: Context to restore
            version_id: Version to restore to
            user_id: User performing the restore
            
        Returns:
            ContextVersion: New version created for the restore operation
        """
        logger.info(f"Restoring context {context_id} to version {version_id} by user {user_id}")
        
        try:
            # Get and validate the version to restore
            version_to_restore = db.session.get(ContextVersion, version_id)
            if not version_to_restore or version_to_restore.context_id != context_id:
                raise ValueError(f"Version {version_id} not found for context {context_id}")
            
            # Verify version integrity before restore
            if not version_to_restore.verify_integrity():
                raise ValueError(f"Version {version_id} has integrity issues, cannot restore")
            
            # Get the context
            from models import Context
            context = db.session.get(Context, context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            # Create backup of current state before restore
            backup_version = ContextVersionService.create_version(
                context, user_id, f"Backup before restore to v{version_to_restore.version_number}",
                version_type='backup'
            )
            
            # Restore context configuration from version snapshot
            config_snapshot = version_to_restore.get_config_snapshot()
            context.set_config(config_snapshot)
            context.chunk_strategy = version_to_restore.chunk_strategy
            context.embedding_model = version_to_restore.embedding_model
            
            # Create new version for the restoration
            restore_changes = {
                'restore_operation': {
                    'operation': 'restore',
                    'restored_from_version': version_to_restore.version_number,
                    'backup_version_created': backup_version.version_number,
                    'restored_at': datetime.now(timezone.utc).isoformat(),
                    'impact_score': 8  # Restores are significant changes
                }
            }
            
            restored_version = ContextVersionService.create_version(
                context=context,
                user_id=user_id,
                description=f"Restored from version {version_to_restore.version_number}",
                version_type='rollback',
                changes=restore_changes
            )
            
            db.session.commit()
            
            logger.info(f"Successfully restored context {context_id} to version {version_to_restore.version_number}")
            return restored_version
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to restore context {context_id} to version {version_id}: {e}")
            log_error_with_context(e, {
                "context_id": context_id,
                "version_id": version_id,
                "user_id": user_id,
                "operation": "restore_version"
            })
            raise
    
    @staticmethod
    def compare_versions(version1_id: int, version2_id: int) -> Dict[str, Any]:
        """
        Comprehensive comparison between two versions
        
        Args:
            version1_id: First version ID
            version2_id: Second version ID
            
        Returns:
            Dict[str, Any]: Detailed comparison results
        """
        logger.debug(f"Comparing versions {version1_id} and {version2_id}")
        
        version1 = db.session.get(ContextVersion, version1_id)
        version2 = db.session.get(ContextVersion, version2_id)
        
        if not version1 or not version2:
            raise ValueError("One or both versions not found")
        
        # Get snapshots for comparison
        config1 = version1.get_config_snapshot()
        config2 = version2.get_config_snapshot()
        docs1 = version1.get_documents_snapshot()
        docs2 = version2.get_documents_snapshot()
        proc1 = version1.get_processing_snapshot()
        proc2 = version2.get_processing_snapshot()
        
        comparison = {
            'version_info': {
                'version1': {
                    'id': version1.id,
                    'number': version1.version_number,
                    'created_at': version1.created_at.isoformat(),
                    'type': version1.version_type
                },
                'version2': {
                    'id': version2.id,
                    'number': version2.version_number,
                    'created_at': version2.created_at.isoformat(),
                    'type': version2.version_type
                }
            },
            'statistics_comparison': {
                'documents': {
                    'version1': version1.total_documents,
                    'version2': version2.total_documents,
                    'difference': version2.total_documents - version1.total_documents
                },
                'chunks': {
                    'version1': version1.total_chunks,
                    'version2': version2.total_chunks,
                    'difference': version2.total_chunks - version1.total_chunks
                },
                'tokens': {
                    'version1': version1.total_tokens,
                    'version2': version2.total_tokens,
                    'difference': version2.total_tokens - version1.total_tokens
                }
            },
            'configuration_comparison': ContextVersionService._compare_configs(config1, config2),
            'processing_comparison': ContextVersionService._compare_configs(proc1, proc2),
            'document_changes': ContextVersionService._compare_documents(docs1, docs2),
            'integrity_status': {
                'version1_valid': version1.verify_integrity(),
                'version2_valid': version2.verify_integrity()
            }
        }
        
        return comparison
    
    @staticmethod
    def _compare_configs(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two configuration dictionaries with detailed analysis"""
        changes = {}
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 != val2:
                if key not in config1:
                    change_type = 'added'
                elif key not in config2:
                    change_type = 'removed'
                else:
                    change_type = 'modified'
                
                changes[key] = {
                    'from': val1,
                    'to': val2,
                    'change_type': change_type
                }
        
        return changes
    
    @staticmethod
    def _compare_documents(docs1: List[Dict[str, Any]], docs2: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare document lists between versions"""
        # Create document ID mappings
        docs1_by_id = {doc['id']: doc for doc in docs1}
        docs2_by_id = {doc['id']: doc for doc in docs2}
        
        ids1 = set(docs1_by_id.keys())
        ids2 = set(docs2_by_id.keys())
        
        return {
            'added_documents': list(ids2 - ids1),
            'removed_documents': list(ids1 - ids2),
            'common_documents': list(ids1 & ids2),
            'document_count_change': len(docs2) - len(docs1)
        }