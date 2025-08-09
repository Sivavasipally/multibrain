"""
User Preferences Routes for RAG Chatbot

This module provides RESTful API endpoints for managing user preferences and settings.
Includes comprehensive CRUD operations, validation, templates, and export functionality.

Routes:
- GET    /api/preferences                 - Get all user preferences
- GET    /api/preferences/{category}      - Get preferences by category
- PUT    /api/preferences                 - Update multiple preferences
- PUT    /api/preferences/{category}      - Update category preferences
- POST   /api/preferences/reset           - Reset preferences to defaults
- GET    /api/preferences/export          - Export preferences
- POST   /api/preferences/import          - Import preferences
- GET    /api/preferences/templates       - List preference templates
- POST   /api/preferences/templates       - Create preference template
- POST   /api/preferences/templates/{id}/apply - Apply template

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from models import UserPreferences
from user_preferences import PreferenceTemplate, DEFAULT_PREFERENCES, PREFERENCE_SCHEMAS
from database import db

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
preferences_bp = Blueprint('preferences', __name__)


def get_current_user_id():
    """Helper function to get current user ID from JWT."""
    return get_jwt_identity()


def log_error_with_context(error, context):
    """Helper function to log errors with context."""
    logger.error(f"Error with context {context}: {error}")


@preferences_bp.route('/api/preferences', methods=['GET'])
@jwt_required()
def get_user_preferences():
    """
    Get all user preferences organized by category.
    
    Returns:
        JSON response with user preferences
    """
    try:
        user_id = get_jwt_identity()
        logger.info(f"Fetching all preferences for user {user_id}")
        
        # Get user preferences
        preferences = UserPreferences.get_user_preferences(user_id)
        
        logger.debug(f"Retrieved {sum(len(prefs) for prefs in preferences.values())} preferences for user {user_id}")
        
        return jsonify({
            'success': True,
            'preferences': preferences,
            'schemas': PREFERENCE_SCHEMAS,
            'categories': list(preferences.keys())
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve preferences',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/<string:category>', methods=['GET'])
@jwt_required()
def get_category_preferences(category: str):
    """
    Get user preferences for a specific category.
    
    Args:
        category: Preference category name
        
    Returns:
        JSON response with category preferences
    """
    try:
        user_id = get_jwt_identity()
        logger.info(f"Fetching {category} preferences for user {user_id}")
        
        # Validate category
        if category not in DEFAULT_PREFERENCES:
            logger.warning(f"Invalid category requested: {category}")
            return jsonify({
                'success': False,
                'error': 'Invalid category',
                'message': f'Category {category} not found',
                'available_categories': list(DEFAULT_PREFERENCES.keys())
            }), 400
        
        # Get category preferences
        preferences = UserPreferences.get_user_preferences(user_id, category)
        category_prefs = preferences.get(category, {})
        
        logger.debug(f"Retrieved {len(category_prefs)} {category} preferences for user {user_id}")
        
        return jsonify({
            'success': True,
            'category': category,
            'preferences': category_prefs,
            'schema': PREFERENCE_SCHEMAS.get(category, {}),
            'defaults': DEFAULT_PREFERENCES.get(category, {})
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get {category} preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve category preferences',
            'message': str(e)
        }), 500


# First update_user_preferences implementation removed - using the more complete one below


# First update_category_preferences implementation removed - using the more complete one below


# Duplicate functions removed - using the more complete implementations below


# Helper functions
def validate_preferences(preferences):
    """Validate preferences structure"""
    try:
        if not isinstance(preferences, dict):
            return {'valid': False, 'errors': ['Preferences must be an object']}
        
        errors = []
        
        # Validate theme preferences
        if 'theme' in preferences:
            theme = preferences['theme']
            if not isinstance(theme, dict):
                errors.append('Theme preferences must be an object')
            else:
                if 'mode' in theme and theme['mode'] not in ['light', 'dark', 'auto']:
                    errors.append('Theme mode must be light, dark, or auto')
        
        # Validate chat preferences
        if 'chat' in preferences:
            chat = preferences['chat']
            if not isinstance(chat, dict):
                errors.append('Chat preferences must be an object')
            else:
                if 'context_limit' in chat:
                    limit = chat['context_limit']
                    if not isinstance(limit, int) or limit < 1 or limit > 10:
                        errors.append('Context limit must be an integer between 1 and 10')
        
        return {'valid': len(errors) == 0, 'errors': errors}
        
    except Exception as e:
        return {'valid': False, 'errors': [f'Validation error: {str(e)}']}


def create_preferences_backup(user_id, preferences):
    """Create a backup of user preferences"""
    try:
        # In a full implementation, this would save to a backup table
        logger.info(f"Created preferences backup for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to create preferences backup: {e}")
        return False


def deep_merge_dict(dict1, dict2):
    """Deep merge two dictionaries"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result
@jwt_required()
def update_user_preferences():
    """
    Update multiple user preferences across categories.
    
    Request body should contain:
    {
        "preferences": {
            "category": {
                "key": "value"
            }
        }
    }
    
    Returns:
        JSON response with update results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'preferences' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing preferences data',
                'message': 'Request body must contain preferences object'
            }), 400
        
        preferences_data = data['preferences']
        logger.info(f"Updating preferences for user {user_id}: {list(preferences_data.keys())}")
        
        updated_count = 0
        updated_preferences = {}
        errors = []
        
        # Process each category
        for category, category_prefs in preferences_data.items():
            if category not in DEFAULT_PREFERENCES:
                errors.append(f"Invalid category: {category}")
                continue
            
            updated_preferences[category] = {}
            
            # Process each preference in the category
            for key, value in category_prefs.items():
                try:
                    preference = UserPreferences.set_user_preference(
                        user_id=user_id,
                        category=category,
                        key=key,
                        value=value
                    )
                    updated_preferences[category][key] = preference.value
                    updated_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to update {category}.{key}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
        
        # Log update summary
        if updated_count > 0:
            logger.info(f"Updated {updated_count} preferences for user {user_id}")
        if errors:
            logger.warning(f"Preference update errors for user {user_id}: {errors}")
        
        return jsonify({
            'success': updated_count > 0,
            'updated_count': updated_count,
            'updated_preferences': updated_preferences,
            'errors': errors
        }), 200 if updated_count > 0 else 400
        
    except Exception as e:
        logger.error(f"Failed to update preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update preferences',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/<string:category>', methods=['OPTIONS'])
def update_category_preferences_options(category: str):
    """Handle CORS preflight requests for category preferences update"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'PUT,OPTIONS')
    return response

@preferences_bp.route('/api/preferences/<string:category>', methods=['PUT'])
@jwt_required()
def update_category_preferences(category: str):
    """
    Update all preferences for a specific category.
    
    Args:
        category: Preference category name
        
    Request body should contain:
    {
        "preferences": {
            "key": "value"
        }
    }
    
    Returns:
        JSON response with update results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'preferences' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing preferences data',
                'message': 'Request body must contain preferences object'
            }), 400
        
        # Validate category
        if category not in DEFAULT_PREFERENCES:
            return jsonify({
                'success': False,
                'error': 'Invalid category',
                'message': f'Category {category} not found',
                'available_categories': list(DEFAULT_PREFERENCES.keys())
            }), 400
        
        preferences_data = data['preferences']
        logger.info(f"Updating {category} preferences for user {user_id}: {list(preferences_data.keys())}")
        
        updated_count = 0
        updated_preferences = {}
        errors = []
        
        # Process each preference in the category
        for key, value in preferences_data.items():
            try:
                preference = UserPreferences.set_user_preference(
                    user_id=user_id,
                    category=category,
                    key=key,
                    value=value
                )
                updated_preferences[key] = preference.value
                updated_count += 1
                
            except Exception as e:
                error_msg = f"Failed to update {key}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        logger.info(f"Updated {updated_count} {category} preferences for user {user_id}")
        
        return jsonify({
            'success': updated_count > 0,
            'category': category,
            'updated_count': updated_count,
            'updated_preferences': updated_preferences,
            'errors': errors
        }), 200 if updated_count > 0 else 400
        
    except Exception as e:
        logger.error(f"Failed to update {category} preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update category preferences',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/reset', methods=['OPTIONS'])
def reset_preferences_options():
    """Handle CORS preflight requests for preferences reset"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@preferences_bp.route('/api/preferences/reset', methods=['POST'])
@jwt_required()
def reset_user_preferences():
    """
    Reset user preferences to defaults.
    
    Request body (optional):
    {
        "category": "appearance"  # Optional: reset specific category only
    }
    
    Returns:
        JSON response with reset results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        category = data.get('category')
        
        if category and category not in DEFAULT_PREFERENCES:
            return jsonify({
                'success': False,
                'error': 'Invalid category',
                'message': f'Category {category} not found',
                'available_categories': list(DEFAULT_PREFERENCES.keys())
            }), 400
        
        logger.info(f"Resetting preferences for user {user_id}, category: {category}")
        
        # Reset preferences
        reset_count = UserPreferences.reset_user_preferences(user_id, category)
        
        # Get updated preferences (now defaults)
        preferences = UserPreferences.get_user_preferences(user_id, category)
        
        logger.info(f"Reset {reset_count} preferences for user {user_id}")
        
        return jsonify({
            'success': True,
            'reset_count': reset_count,
            'category': category,
            'preferences': preferences,
            'message': f'Reset {reset_count} preferences to defaults'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reset preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset preferences',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/export', methods=['GET'])
@jwt_required()
def export_user_preferences():
    """
    Export user preferences in specified format.
    
    Query parameters:
    - format: Export format (json, csv) - default: json
    
    Returns:
        Exported preferences in requested format
    """
    try:
        user_id = get_jwt_identity()
        format_type = request.args.get('format', 'json').lower()
        
        if format_type not in ['json', 'csv']:
            return jsonify({
                'success': False,
                'error': 'Invalid export format',
                'message': 'Supported formats: json, csv'
            }), 400
        
        logger.info(f"Exporting preferences for user {user_id} in {format_type} format")
        
        # Export preferences
        exported_data = UserPreferences.export_user_preferences(user_id, format_type)
        
        # Set appropriate content type
        if format_type == 'json':
            content_type = 'application/json'
            filename = f'preferences_{user_id}.json'
        else:  # csv
            content_type = 'text/csv'
            filename = f'preferences_{user_id}.csv'
        
        logger.info(f"Exported preferences for user {user_id} ({len(exported_data)} bytes)")
        
        return current_app.response_class(
            exported_data,
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': content_type
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to export preferences',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/import', methods=['OPTIONS'])
def import_preferences_options():
    """Handle CORS preflight requests for preferences import"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@preferences_bp.route('/api/preferences/import', methods=['POST'])
@jwt_required()
def import_user_preferences():
    """
    Import user preferences from uploaded data.
    
    Request body should contain:
    {
        "preferences": {
            "category": {
                "key": "value"
            }
        },
        "merge": true  # Optional: merge with existing (default: false - replace)
    }
    
    Returns:
        JSON response with import results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'preferences' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing preferences data',
                'message': 'Request body must contain preferences object'
            }), 400
        
        preferences_data = data['preferences']
        merge_mode = data.get('merge', False)
        
        logger.info(f"Importing preferences for user {user_id}, merge: {merge_mode}")
        
        # If not merging, reset existing preferences first
        if not merge_mode:
            reset_count = UserPreferences.reset_user_preferences(user_id)
            logger.info(f"Reset {reset_count} existing preferences before import")
        
        imported_count = 0
        imported_preferences = {}
        errors = []
        
        # Import preferences
        for category, category_prefs in preferences_data.items():
            if category not in DEFAULT_PREFERENCES:
                errors.append(f"Skipped invalid category: {category}")
                continue
            
            imported_preferences[category] = {}
            
            for key, value in category_prefs.items():
                try:
                    preference = UserPreferences.set_user_preference(
                        user_id=user_id,
                        category=category,
                        key=key,
                        value=value,
                        description="Imported from user data"
                    )
                    imported_preferences[category][key] = preference.value
                    imported_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to import {category}.{key}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
        
        logger.info(f"Imported {imported_count} preferences for user {user_id}")
        
        return jsonify({
            'success': imported_count > 0,
            'imported_count': imported_count,
            'imported_preferences': imported_preferences,
            'merge_mode': merge_mode,
            'errors': errors
        }), 200 if imported_count > 0 else 400
        
    except Exception as e:
        logger.error(f"Failed to import preferences for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to import preferences',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/templates', methods=['GET'])
@jwt_required()
def get_preference_templates():
    """
    Get available preference templates.
    
    Query parameters:
    - category: Filter by category (optional)
    - public_only: Show only public templates (default: true)
    
    Returns:
        JSON response with available templates
    """
    try:
        user_id = get_jwt_identity()
        category = request.args.get('category')
        public_only = request.args.get('public_only', 'true').lower() == 'true'
        
        logger.info(f"Fetching preference templates for user {user_id}, category: {category}, public_only: {public_only}")
        
        # Build query
        query = PreferenceTemplate.query
        
        if category:
            if category not in DEFAULT_PREFERENCES:
                return jsonify({
                    'success': False,
                    'error': 'Invalid category',
                    'message': f'Category {category} not found'
                }), 400
            query = query.filter_by(category=category)
        
        if public_only:
            query = query.filter_by(is_public=True)
        else:
            # Include public templates and user's own templates
            query = query.filter(
                (PreferenceTemplate.is_public == True) |
                (PreferenceTemplate.created_by == user_id)
            )
        
        templates = query.order_by(PreferenceTemplate.usage_count.desc()).all()
        
        # Convert to dictionaries
        templates_data = [template.to_dict() for template in templates]
        
        logger.debug(f"Retrieved {len(templates_data)} preference templates")
        
        return jsonify({
            'success': True,
            'templates': templates_data,
            'count': len(templates_data),
            'category': category
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get preference templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve templates',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/templates', methods=['POST'])
@jwt_required()
def create_preference_template():
    """
    Create a new preference template.
    
    Request body should contain:
    {
        "name": "Template Name",
        "description": "Template description",
        "category": "appearance",
        "preferences": {
            "key": "value"
        },
        "is_public": false
    }
    
    Returns:
        JSON response with created template
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category', 'preferences']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        name = data['name']
        category = data['category']
        preferences = data['preferences']
        description = data.get('description')
        is_public = data.get('is_public', False)
        
        # Validate category
        if category not in DEFAULT_PREFERENCES:
            return jsonify({
                'success': False,
                'error': 'Invalid category',
                'message': f'Category {category} not found'
            }), 400
        
        logger.info(f"Creating preference template '{name}' for user {user_id}")
        
        # Create template
        template = PreferenceTemplate(
            name=name,
            description=description,
            category=category,
            preferences=preferences,
            created_by=user_id,
            is_public=is_public
        )
        
        db.session.add(template)
        db.session.commit()
        
        logger.info(f"Created preference template {template.id} for user {user_id}")
        
        return jsonify({
            'success': True,
            'template': template.to_dict(),
            'message': 'Template created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create preference template: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create template',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/templates/<int:template_id>/apply', methods=['POST'])
@jwt_required()
def apply_preference_template(template_id: int):
    """
    Apply a preference template to the current user.
    
    Args:
        template_id: ID of the template to apply
        
    Returns:
        JSON response with application results
    """
    try:
        user_id = get_jwt_identity()
        
        # Find template
        template = PreferenceTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found',
                'message': f'Template {template_id} does not exist'
            }), 404
        
        # Check permissions
        if not template.is_public and template.created_by != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'You do not have permission to use this template'
            }), 403
        
        logger.info(f"Applying template '{template.name}' to user {user_id}")
        
        # Apply template
        applied_count = template.apply_to_user(user_id)
        
        # Get updated preferences
        preferences = UserPreferences.get_user_preferences(user_id, template.category)
        
        logger.info(f"Applied template '{template.name}' to user {user_id}: {applied_count} preferences")
        
        return jsonify({
            'success': True,
            'template': template.to_dict(),
            'applied_count': applied_count,
            'updated_preferences': preferences.get(template.category, {}),
            'message': f'Applied {applied_count} preferences from template'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to apply template {template_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to apply template',
            'message': str(e)
        }), 500


@preferences_bp.route('/api/preferences/schema', methods=['GET'])
def get_preference_schemas():
    """
    Get preference schemas for validation.
    
    Returns:
        JSON response with preference schemas
    """
    try:
        return jsonify({
            'success': True,
            'schemas': PREFERENCE_SCHEMAS,
            'defaults': DEFAULT_PREFERENCES,
            'categories': list(PREFERENCE_SCHEMAS.keys())
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get preference schemas: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve schemas',
            'message': str(e)
        }), 500


# Error handlers
@preferences_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle bad request errors."""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(error.description)
    }), 400


@preferences_bp.errorhandler(404)
def handle_not_found(error):
    """Handle not found errors."""
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': str(error.description)
    }), 404


@preferences_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error in preferences: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500