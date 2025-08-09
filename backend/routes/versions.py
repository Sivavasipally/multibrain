"""
Context Versioning API Routes for RAG Chatbot PWA

This module provides RESTful API endpoints for managing context versions,
including version creation, comparison, rollback, and history management.
The versioning system allows users to track changes to their knowledge bases
and restore previous states when needed.

Key Features:
- Version history and timeline view
- Manual and automatic version creation
- Version comparison and diff analysis
- Rollback and restore functionality
- Version tagging and categorization
- Integrity verification and validation

API Endpoints:
- GET /contexts/{id}/versions: Get version history
- POST /contexts/{id}/versions: Create new version
- GET /versions/{id}: Get specific version details
- POST /versions/{id}/restore: Restore to version
- GET /versions/{id1}/compare/{id2}: Compare versions
- POST /versions/{id}/tags: Add version tag
- DELETE /versions/{id}: Delete version (with protection)

Security Features:
- User ownership validation
- Admin privilege checking for sensitive operations
- Comprehensive audit logging
- Input validation and sanitization
- Rate limiting for version operations

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Context, User
from context_versioning import ContextVersion, ContextVersionService, VersionTag, ContextVersionDiff
from sqlalchemy import desc
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('version_routes')

def get_current_user_id():
    """
    Extract and validate user ID from JWT token for version operations
    
    Returns:
        int: The authenticated user's ID if valid token exists
        None: If no token or invalid token
    """
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved user ID {user_id} for version operation")
            return user_id
        else:
            logger.debug("No user identity found in JWT token for version operation")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer for version operation: {e}")
        return None

def validate_context_ownership(context_id: int, user_id: int) -> bool:
    """
    Validate that user owns the context
    
    Args:
        context_id: Context ID to validate
        user_id: User ID to check ownership
        
    Returns:
        bool: True if user owns context, False otherwise
    """
    context = db.session.get(Context, context_id)
    return context and context.user_id == user_id

versions_bp = Blueprint('versions', __name__)

@versions_bp.route('/contexts/<int:context_id>/versions', methods=['GET'])
@jwt_required()
def get_version_history(context_id: int):
    """
    Get comprehensive version history for a context
    
    Retrieves the complete version history for a knowledge base including
    version metadata, statistics, tags, and change summaries. Supports
    pagination and filtering for efficient browsing of large histories.
    
    Query Parameters:
        limit (int, optional): Maximum versions to return (default: 20, max: 100)
        offset (int, optional): Number of versions to skip (default: 0)
        version_type (str, optional): Filter by version type (auto, manual, milestone, etc.)
        include_snapshots (bool, optional): Include full snapshot data (default: false)
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        200: Version history successfully retrieved
        {
            "versions": [
                {
                    "id": "Version ID",
                    "version_number": "Semantic version number",
                    "version_type": "Version type",
                    "description": "Change description",
                    "created_at": "ISO timestamp",
                    "created_by": "User ID",
                    "total_documents": "Document count",
                    "total_chunks": "Chunk count", 
                    "total_tokens": "Token count",
                    "change_impact": "Impact level",
                    "integrity_verified": true/false,
                    "is_current": true/false,
                    "tags": ["Version tags"]
                }
            ],
            "pagination": {
                "total": "Total version count",
                "limit": "Items per page",
                "offset": "Items skipped",
                "has_more": true/false
            }
        }
        
        403: Insufficient permissions (not context owner)
        404: Context not found
        500: Server error during history retrieval
        
    Example:
        curl -X GET "/api/contexts/123/versions?limit=10&version_type=manual" \
             -H "Authorization: Bearer <jwt_token>"
    """
    client_ip = request.remote_addr
    user_id = get_current_user_id()
    
    if not user_id:
        logger.warning(f"Version history request with invalid JWT from {client_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    logger.info(f"Version history request for context {context_id} from user {user_id} at {client_ip}")
    
    # Validate context ownership
    if not validate_context_ownership(context_id, user_id):
        logger.warning(f"Unauthorized version history access attempt for context {context_id} by user {user_id}")
        return jsonify({'error': 'Context not found or access denied'}), 403
    
    try:
        # Parse query parameters
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)
        version_type = request.args.get('version_type')
        include_snapshots = request.args.get('include_snapshots', 'false').lower() == 'true'
        
        logger.debug(f"Version history query: limit={limit}, offset={offset}, type={version_type}")
        
        # Build query
        query = ContextVersion.query.filter_by(context_id=context_id)
        
        if version_type:
            query = query.filter_by(version_type=version_type)
        
        # Get total count before pagination
        total_versions = query.count()
        
        # Apply pagination and ordering
        versions = query.order_by(desc(ContextVersion.created_at))\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
        
        # Convert to response format
        version_data = []
        for version in versions:
            version_dict = version.to_dict(include_snapshots=include_snapshots)
            
            # Add creator information
            if version.created_by:
                creator = db.session.get(User, version.created_by)
                if creator:
                    version_dict['created_by_username'] = creator.username
            
            version_data.append(version_dict)
        
        response_data = {
            'versions': version_data,
            'pagination': {
                'total': total_versions,
                'limit': limit,
                'offset': offset,
                'has_more': offset + len(versions) < total_versions
            },
            'context_id': context_id
        }
        
        logger.info(f"Retrieved {len(version_data)} versions for context {context_id} (total: {total_versions})")
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = f"Failed to retrieve version history for context {context_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "context_id": context_id,
            "user_id": user_id,
            "client_ip": client_ip,
            "operation": "get_version_history"
        })
        return jsonify({'error': 'Failed to retrieve version history'}), 500

@versions_bp.route('/contexts/<int:context_id>/versions', methods=['POST'])
@jwt_required()
def create_version(context_id: int):
    """
    Create a new manual version of a context
    
    Creates a new version snapshot of the current context state with user-provided
    description and metadata. This endpoint is used for manual versioning when
    users want to create checkpoints before major changes.
    
    Request Body:
        {
            "description": "Description of this version",
            "version_type": "manual|milestone|backup",
            "force_major": true/false,
            "tags": [
                {
                    "tag_name": "Tag name", 
                    "tag_description": "Tag description",
                    "tag_type": "user|milestone|release",
                    "tag_color": "#hex_color"
                }
            ],
            "changes": {
                "change_type": {
                    "operation": "added|modified|removed",
                    "description": "Change description",
                    "impact_score": 1-10
                }
            }
        }
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        201: Version successfully created
        {
            "version": {
                "id": "New version ID",
                "version_number": "Assigned version number",
                "description": "Version description",
                "created_at": "ISO timestamp",
                "content_hash": "Integrity hash",
                "total_documents": "Document count",
                "total_chunks": "Chunk count"
            },
            "message": "Version created successfully"
        }
        
        400: Invalid request data
        403: Insufficient permissions
        500: Version creation failed
        
    Example:
        curl -X POST "/api/contexts/123/versions" \
             -H "Authorization: Bearer <jwt_token>" \
             -H "Content-Type: application/json" \
             -d '{"description":"Before major refactoring","version_type":"milestone"}'
    """
    client_ip = request.remote_addr
    user_id = get_current_user_id()
    
    if not user_id:
        logger.warning(f"Version creation request with invalid JWT from {client_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    logger.info(f"Manual version creation request for context {context_id} from user {user_id}")
    
    # Validate context ownership
    if not validate_context_ownership(context_id, user_id):
        logger.warning(f"Unauthorized version creation attempt for context {context_id} by user {user_id}")
        return jsonify({'error': 'Context not found or access denied'}), 403
    
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        description = data.get('description', 'Manual version')
        version_type = data.get('version_type', 'manual')
        force_major = data.get('force_major', False)
        changes = data.get('changes', {})
        tags_data = data.get('tags', [])
        
        # Validate version type
        valid_types = ['manual', 'milestone', 'backup']
        if version_type not in valid_types:
            return jsonify({'error': f'Invalid version type. Must be one of: {", ".join(valid_types)}'}), 400
        
        # Get the context
        context = db.session.get(Context, context_id)
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        logger.debug(f"Creating {version_type} version for context {context_id}: {description}")
        
        # Create the version
        version = ContextVersionService.create_version(
            context=context,
            user_id=user_id,
            description=description,
            version_type=version_type,
            changes=changes,
            force_major=force_major
        )
        
        # Add tags if provided
        for tag_info in tags_data:
            if isinstance(tag_info, dict) and 'tag_name' in tag_info:
                tag = VersionTag(
                    version_id=version.id,
                    tag_name=tag_info['tag_name'],
                    tag_description=tag_info.get('tag_description'),
                    tag_type=tag_info.get('tag_type', 'user'),
                    tag_color=tag_info.get('tag_color', '#007bff'),
                    created_by=user_id
                )
                db.session.add(tag)
        
        db.session.commit()
        
        response_data = {
            'version': version.to_dict(),
            'message': f'Version {version.version_number} created successfully'
        }
        
        logger.info(f"Successfully created version {version.version_number} for context {context_id}")
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Failed to create version for context {context_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "context_id": context_id,
            "user_id": user_id,
            "version_type": version_type if 'version_type' in locals() else None,
            "operation": "create_version"
        })
        return jsonify({'error': 'Version creation failed'}), 500

@versions_bp.route('/versions/<int:version_id>', methods=['GET'])
@jwt_required()
def get_version_details(version_id: int):
    """
    Get detailed information about a specific version
    
    Retrieves comprehensive information about a version including snapshots,
    diffs, tags, and integrity status. Used for version inspection and
    detailed analysis before restore operations.
    
    Query Parameters:
        include_snapshots (bool, optional): Include full snapshot data
        include_diffs (bool, optional): Include change diffs
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        200: Version details successfully retrieved
        404: Version not found or access denied
        500: Server error
        
    Example:
        curl -X GET "/api/versions/456?include_snapshots=true" \
             -H "Authorization: Bearer <jwt_token>"
    """
    client_ip = request.remote_addr
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    logger.debug(f"Version details request for version {version_id} from user {user_id}")
    
    try:
        # Get version and validate access
        version = db.session.get(ContextVersion, version_id)
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        # Validate context ownership
        if not validate_context_ownership(version.context_id, user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Parse query parameters
        include_snapshots = request.args.get('include_snapshots', 'false').lower() == 'true'
        include_diffs = request.args.get('include_diffs', 'false').lower() == 'true'
        
        # Build response
        version_data = version.to_dict(include_snapshots=include_snapshots)
        
        # Add creator information
        if version.created_by:
            creator = db.session.get(User, version.created_by)
            if creator:
                version_data['created_by_username'] = creator.username
        
        # Add diffs if requested
        if include_diffs:
            diffs = ContextVersionDiff.query.filter_by(version_id=version_id).all()
            version_data['diffs'] = [diff.to_dict() for diff in diffs]
        
        return jsonify({'version': version_data}), 200
        
    except Exception as e:
        error_msg = f"Failed to retrieve version {version_id} details: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "version_id": version_id,
            "user_id": user_id,
            "operation": "get_version_details"
        })
        return jsonify({'error': 'Failed to retrieve version details'}), 500

@versions_bp.route('/versions/<int:version_id>/restore', methods=['POST'])
@jwt_required()
def restore_version(version_id: int):
    """
    Restore a context to a specific version
    
    Performs a rollback operation to restore a context to a previous version.
    Creates a backup of the current state before restore and performs integrity
    checks to ensure safe rollback operations.
    
    Request Body:
        {
            "confirm": true,
            "backup_description": "Pre-restore backup description"
        }
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        200: Restore operation successful
        400: Invalid request or confirmation required
        403: Insufficient permissions
        409: Version integrity issues
        500: Restore operation failed
        
    Example:
        curl -X POST "/api/versions/456/restore" \
             -H "Authorization: Bearer <jwt_token>" \
             -H "Content-Type: application/json" \
             -d '{"confirm":true}'
    """
    client_ip = request.remote_addr
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    logger.info(f"Version restore request for version {version_id} from user {user_id}")
    
    try:
        # Get version and validate
        version = db.session.get(ContextVersion, version_id)
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        # Validate context ownership
        if not validate_context_ownership(version.context_id, user_id):
            logger.warning(f"Unauthorized restore attempt for version {version_id} by user {user_id}")
            return jsonify({'error': 'Access denied'}), 403
        
        # Parse request data
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'error': 'Restore confirmation required',
                'message': 'Set "confirm": true to proceed with restore operation'
            }), 400
        
        # Verify version integrity
        if not version.verify_integrity():
            logger.error(f"Cannot restore version {version_id} due to integrity issues")
            return jsonify({
                'error': 'Version integrity check failed',
                'message': 'This version appears to be corrupted and cannot be restored'
            }), 409
        
        logger.warning(f"RESTORE OPERATION: User {user_id} restoring context {version.context_id} to version {version.version_number}")
        
        # Perform the restore
        restored_version = ContextVersionService.restore_version(
            context_id=version.context_id,
            version_id=version_id,
            user_id=user_id
        )
        
        response_data = {
            'message': f'Successfully restored to version {version.version_number}',
            'restored_version': restored_version.to_dict(),
            'original_version': version.to_dict()
        }
        
        logger.info(f"Successfully restored context {version.context_id} to version {version.version_number}")
        return jsonify(response_data), 200
        
    except ValueError as ve:
        logger.error(f"Validation error during restore: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        error_msg = f"Failed to restore version {version_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "version_id": version_id,
            "user_id": user_id,
            "operation": "restore_version"
        })
        return jsonify({'error': 'Restore operation failed'}), 500

@versions_bp.route('/versions/<int:version1_id>/compare/<int:version2_id>', methods=['GET'])
@jwt_required()
def compare_versions(version1_id: int, version2_id: int):
    """
    Compare two versions and show differences
    
    Provides detailed comparison between two versions including configuration
    changes, document modifications, and statistical differences. Used for
    change analysis and impact assessment.
    
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        200: Comparison completed successfully
        403: Access denied to one or both versions
        404: One or both versions not found
        500: Comparison failed
        
    Example:
        curl -X GET "/api/versions/456/compare/789" \
             -H "Authorization: Bearer <jwt_token>"
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    logger.debug(f"Version comparison request: {version1_id} vs {version2_id} by user {user_id}")
    
    try:
        # Get both versions
        version1 = db.session.get(ContextVersion, version1_id)
        version2 = db.session.get(ContextVersion, version2_id)
        
        if not version1 or not version2:
            return jsonify({'error': 'One or both versions not found'}), 404
        
        # Validate access to both contexts
        if (not validate_context_ownership(version1.context_id, user_id) or 
            not validate_context_ownership(version2.context_id, user_id)):
            return jsonify({'error': 'Access denied'}), 403
        
        # Perform comparison
        comparison = ContextVersionService.compare_versions(version1_id, version2_id)
        
        return jsonify({'comparison': comparison}), 200
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        error_msg = f"Failed to compare versions {version1_id} and {version2_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "version1_id": version1_id,
            "version2_id": version2_id,
            "user_id": user_id,
            "operation": "compare_versions"
        })
        return jsonify({'error': 'Version comparison failed'}), 500

@versions_bp.route('/versions/<int:version_id>/tags', methods=['POST'])
@jwt_required()
def add_version_tag(version_id: int):
    """
    Add a tag to a version
    
    Creates a named tag for a version to make it easier to reference and
    categorize. Tags can have different types and colors for organization.
    
    Request Body:
        {
            "tag_name": "Tag name (required)",
            "tag_description": "Tag description",
            "tag_type": "user|system|milestone|release|backup",
            "tag_color": "#hex_color"
        }
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        201: Tag added successfully
        400: Invalid request data or tag already exists
        403: Access denied
        404: Version not found
        500: Tag creation failed
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get version and validate access
        version = db.session.get(ContextVersion, version_id)
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        if not validate_context_ownership(version.context_id, user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Parse request data
        data = request.get_json()
        if not data or 'tag_name' not in data:
            return jsonify({'error': 'tag_name is required'}), 400
        
        tag_name = data['tag_name'].strip()
        if not tag_name:
            return jsonify({'error': 'tag_name cannot be empty'}), 400
        
        # Check if tag already exists
        existing_tag = VersionTag.query.filter_by(
            version_id=version_id, tag_name=tag_name
        ).first()
        
        if existing_tag:
            return jsonify({'error': 'Tag already exists for this version'}), 400
        
        # Create new tag
        tag = VersionTag(
            version_id=version_id,
            tag_name=tag_name,
            tag_description=data.get('tag_description'),
            tag_type=data.get('tag_type', 'user'),
            tag_color=data.get('tag_color', '#007bff'),
            created_by=user_id
        )
        
        db.session.add(tag)
        db.session.commit()
        
        logger.info(f"Added tag '{tag_name}' to version {version_id} by user {user_id}")
        
        return jsonify({
            'message': 'Tag added successfully',
            'tag': tag.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Failed to add tag to version {version_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "version_id": version_id,
            "user_id": user_id,
            "operation": "add_version_tag"
        })
        return jsonify({'error': 'Tag creation failed'}), 500

@versions_bp.route('/versions/<int:version_id>', methods=['DELETE'])
@jwt_required()
def delete_version(version_id: int):
    """
    Delete a version (with protection checks)
    
    Deletes a version if it's not protected and not the current version.
    Includes safety checks to prevent accidental deletion of important versions.
    
    Query Parameters:
        force (bool, optional): Force deletion even if protected (admin only)
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        200: Version deleted successfully
        400: Cannot delete protected or current version
        403: Access denied or insufficient permissions
        404: Version not found
        500: Deletion failed
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get version and validate access
        version = db.session.get(ContextVersion, version_id)
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        if not validate_context_ownership(version.context_id, user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check protection status
        force = request.args.get('force', 'false').lower() == 'true'
        
        if version.is_current:
            return jsonify({
                'error': 'Cannot delete current version',
                'message': 'Create or restore another version first'
            }), 400
        
        if version.is_protected and not force:
            return jsonify({
                'error': 'Version is protected from deletion',
                'message': 'Use force=true parameter to override protection'
            }), 400
        
        # For force deletion, check admin privileges
        if force:
            user = db.session.get(User, user_id)
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin privileges required for force deletion'}), 403
        
        logger.warning(f"Deleting version {version_id} (v{version.version_number}) by user {user_id}, force={force}")
        
        # Delete the version and related records
        db.session.delete(version)
        db.session.commit()
        
        logger.info(f"Successfully deleted version {version_id}")
        
        return jsonify({
            'message': f'Version {version.version_number} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Failed to delete version {version_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "version_id": version_id,
            "user_id": user_id,
            "operation": "delete_version"
        })
        return jsonify({'error': 'Version deletion failed'}), 500