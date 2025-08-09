"""
Background Task Management API Routes for RAG Chatbot PWA

This module provides RESTful API endpoints for managing background tasks,
including task submission, monitoring, and result retrieval. These routes
allow users to submit long-running operations and track their progress.

Key Features:
- Task submission with priority and scheduling
- Real-time progress monitoring
- Task result retrieval
- User-specific task filtering
- Task cancellation and management
- System task statistics and monitoring

API Endpoints:
- POST /tasks: Submit new background task
- GET /tasks: Get user's tasks with filtering
- GET /tasks/{id}: Get specific task details
- DELETE /tasks/{id}: Cancel pending task
- GET /tasks/stats: Get task system statistics
- GET /contexts/{id}/tasks: Get tasks for context

Security Features:
- JWT authentication for all endpoints
- User ownership validation for tasks
- Admin privileges for system operations
- Comprehensive audit logging
- Rate limiting for task submissions

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Import services and models
from services.task_service import task_service, TaskPriority, TaskStatus
from models import db, User, Context

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('task_routes')

# Create blueprint
tasks_bp = Blueprint('tasks', __name__)

def get_current_user_id() -> Optional[int]:
    """Extract and validate user ID from JWT token"""
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved user ID {user_id} for task operation")
            return user_id
        else:
            logger.debug("No user identity found in JWT token for task operation")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer for task operation: {e}")
        return None

def validate_context_ownership(context_id: int, user_id: int) -> bool:
    """Validate that user owns the context"""
    context = db.session.get(Context, context_id)
    return context and context.user_id == user_id

@tasks_bp.route('/tasks', methods=['POST'])
@jwt_required()
def submit_task():
    """
    Submit a new background task
    
    Creates a new background task for asynchronous execution. Supports
    various task types with different priority levels and parameters.
    
    Request Body:
        {
            "task_type": "document_processing|context_reprocessing|version_creation|repository_cloning|cleanup_operations",
            "priority": "low|normal|high|urgent",
            "context_id": 123,
            "parameters": {
                // Task-specific parameters
            }
        }
        
    Authentication:
        Requires valid JWT token
        
    Returns:
        201: Task submitted successfully
        {
            "task_id": "uuid-string",
            "message": "Task submitted successfully",
            "task_type": "document_processing",
            "status": "pending",
            "estimated_duration": "5-10 minutes"
        }
        
        400: Invalid request data
        403: Insufficient permissions
        429: Rate limit exceeded
        500: Task submission failed
        
    Example:
        curl -X POST "/api/tasks" \
             -H "Authorization: Bearer <jwt_token>" \
             -H "Content-Type: application/json" \
             -d '{
               "task_type": "document_processing",
               "priority": "high",
               "context_id": 123
             }'
    """
    client_ip = request.remote_addr
    user_id = get_current_user_id()
    
    if not user_id:
        logger.warning(f"Task submission with invalid JWT from {client_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        task_type = data.get('task_type')
        if not task_type:
            return jsonify({'error': 'task_type is required'}), 400
        
        # Validate task type
        valid_types = ['document_processing', 'context_reprocessing', 'version_creation', 
                      'repository_cloning', 'cleanup_operations']
        if task_type not in valid_types:
            return jsonify({
                'error': f'Invalid task type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Parse priority
        priority_str = data.get('priority', 'normal')
        try:
            priority = TaskPriority[priority_str.upper()]
        except KeyError:
            return jsonify({
                'error': f'Invalid priority. Must be one of: low, normal, high, urgent'
            }), 400
        
        # Get context ID and validate ownership if provided
        context_id = data.get('context_id')
        if context_id:
            if not validate_context_ownership(context_id, user_id):
                logger.warning(f"Unauthorized task submission for context {context_id} by user {user_id}")
                return jsonify({'error': 'Context not found or access denied'}), 403
        
        # Get task parameters
        parameters = data.get('parameters', {})
        
        # Add context_id to parameters if provided
        if context_id:
            parameters['context_id'] = context_id
        
        # Special validation for different task types
        if task_type == 'repository_cloning':
            repo_url = parameters.get('repo_url')
            if not repo_url:
                return jsonify({'error': 'repo_url is required for repository cloning'}), 400
        
        logger.info(f"Submitting {task_type} task for user {user_id}, context {context_id}")
        
        # Submit task
        task_id = task_service.submit_task(
            task_type=task_type,
            priority=priority,
            user_id=user_id,
            context_id=context_id,
            max_retries=data.get('max_retries', 3),
            **parameters
        )
        
        # Estimate duration based on task type
        duration_estimates = {
            'document_processing': '2-10 minutes',
            'context_reprocessing': '5-15 minutes',
            'version_creation': '30 seconds - 2 minutes',
            'repository_cloning': '3-20 minutes',
            'cleanup_operations': '1-5 minutes'
        }
        
        response_data = {
            'task_id': task_id,
            'message': 'Task submitted successfully',
            'task_type': task_type,
            'priority': priority.name.lower(),
            'status': 'pending',
            'estimated_duration': duration_estimates.get(task_type, '1-10 minutes')
        }
        
        logger.info(f"Successfully submitted task {task_id} for user {user_id}")
        return jsonify(response_data), 201
        
    except Exception as e:
        error_msg = f"Failed to submit task: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "user_id": user_id,
            "client_ip": client_ip,
            "task_type": task_type if 'task_type' in locals() else None,
            "operation": "submit_task"
        })
        return jsonify({'error': 'Task submission failed'}), 500

@tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_user_tasks():
    """
    Get user's background tasks
    
    Retrieves tasks submitted by the current user with optional filtering
    and pagination support.
    
    Query Parameters:
        status (str, optional): Filter by status (pending, running, completed, failed, cancelled)
        task_type (str, optional): Filter by task type
        limit (int, optional): Maximum tasks to return (default: 20, max: 100)
        offset (int, optional): Number of tasks to skip
        
    Authentication:
        Requires valid JWT token
        
    Returns:
        200: Tasks retrieved successfully
        {
            "tasks": [
                {
                    "id": "task-uuid",
                    "task_type": "document_processing",
                    "status": "completed",
                    "progress": 100,
                    "created_at": "2024-01-15T10:30:00Z",
                    "completed_at": "2024-01-15T10:35:00Z",
                    "result": {
                        "success": true,
                        "data": {...}
                    }
                }
            ],
            "pagination": {
                "total": 25,
                "limit": 20,
                "offset": 0,
                "has_more": true
            }
        }
        
    Example:
        curl -X GET "/api/tasks?status=running&limit=10" \
             -H "Authorization: Bearer <jwt_token>"
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Parse query parameters
        status_filter = request.args.get('status')
        task_type_filter = request.args.get('task_type')
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)
        
        logger.debug(f"Getting tasks for user {user_id}: status={status_filter}, type={task_type_filter}")
        
        # Get user tasks
        user_tasks = task_service.get_user_tasks(user_id, limit=limit + offset + 50)  # Get more for filtering
        
        # Apply filters
        filtered_tasks = []
        for task_dict in user_tasks:
            # Status filter
            if status_filter and task_dict['status'] != status_filter:
                continue
                
            # Task type filter
            if task_type_filter and task_dict['task_type'] != task_type_filter:
                continue
                
            filtered_tasks.append(task_dict)
        
        # Apply pagination
        total_tasks = len(filtered_tasks)
        paginated_tasks = filtered_tasks[offset:offset + limit]
        
        response_data = {
            'tasks': paginated_tasks,
            'pagination': {
                'total': total_tasks,
                'limit': limit,
                'offset': offset,
                'has_more': offset + len(paginated_tasks) < total_tasks
            }
        }
        
        logger.debug(f"Retrieved {len(paginated_tasks)} tasks for user {user_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = f"Failed to retrieve tasks for user {user_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "user_id": user_id,
            "operation": "get_user_tasks"
        })
        return jsonify({'error': 'Failed to retrieve tasks'}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_details(task_id: str):
    """
    Get specific task details
    
    Retrieves detailed information about a specific task including
    current status, progress, and results if completed.
    
    Authentication:
        Requires valid JWT token and task ownership
        
    Returns:
        200: Task details retrieved successfully
        404: Task not found or access denied
        500: Server error
        
    Example:
        curl -X GET "/api/tasks/uuid-string" \
             -H "Authorization: Bearer <jwt_token>"
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get task details
        task_dict = task_service.get_task(task_id)
        if not task_dict:
            return jsonify({'error': 'Task not found'}), 404
        
        # Validate user ownership
        if task_dict.get('user_id') != user_id:
            logger.warning(f"Unauthorized task access attempt: user {user_id} tried to access task {task_id}")
            return jsonify({'error': 'Task not found'}), 404
        
        logger.debug(f"Retrieved task details for {task_id}")
        return jsonify({'task': task_dict}), 200
        
    except Exception as e:
        error_msg = f"Failed to retrieve task {task_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "task_id": task_id,
            "user_id": user_id,
            "operation": "get_task_details"
        })
        return jsonify({'error': 'Failed to retrieve task details'}), 500

@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
def cancel_task(task_id: str):
    """
    Cancel a pending task
    
    Cancels a task that is still pending (not yet started). Running
    tasks cannot be cancelled through this endpoint.
    
    Authentication:
        Requires valid JWT token and task ownership
        
    Returns:
        200: Task cancelled successfully
        400: Task cannot be cancelled (already running/completed)
        404: Task not found or access denied
        500: Server error
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get task details first
        task_dict = task_service.get_task(task_id)
        if not task_dict:
            return jsonify({'error': 'Task not found'}), 404
        
        # Validate user ownership
        if task_dict.get('user_id') != user_id:
            logger.warning(f"Unauthorized task cancel attempt: user {user_id} tried to cancel task {task_id}")
            return jsonify({'error': 'Task not found'}), 404
        
        # Try to cancel the task
        if task_service.cancel_task(task_id):
            logger.info(f"Successfully cancelled task {task_id} by user {user_id}")
            return jsonify({
                'message': 'Task cancelled successfully',
                'task_id': task_id
            }), 200
        else:
            return jsonify({
                'error': 'Task cannot be cancelled',
                'message': 'Task is already running or completed'
            }), 400
            
    except Exception as e:
        error_msg = f"Failed to cancel task {task_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "task_id": task_id,
            "user_id": user_id,
            "operation": "cancel_task"
        })
        return jsonify({'error': 'Failed to cancel task'}), 500

@tasks_bp.route('/tasks/stats', methods=['GET'])
@jwt_required()
def get_task_stats():
    """
    Get task system statistics
    
    Retrieves system-wide task statistics and metrics. Available to all users
    for their own tasks, with additional system stats for admin users.
    
    Authentication:
        Requires valid JWT token
        
    Returns:
        200: Statistics retrieved successfully
        {
            "user_stats": {
                "total_tasks": 15,
                "status_counts": {
                    "completed": 12,
                    "pending": 1,
                    "running": 2,
                    "failed": 0
                },
                "type_counts": {
                    "document_processing": 10,
                    "version_creation": 5
                }
            },
            "system_stats": {  // Only for admin users
                "workers": 2,
                "running": true,
                "queue_size": 3
            }
        }
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get user's task statistics
        user_tasks = task_service.get_user_tasks(user_id, limit=1000)
        
        user_stats = {
            'total_tasks': len(user_tasks),
            'status_counts': {},
            'type_counts': {}
        }
        
        # Count by status and type
        for status in TaskStatus:
            user_stats['status_counts'][status.value] = 0
            
        for task_dict in user_tasks:
            status = task_dict['status']
            task_type = task_dict['task_type']
            
            user_stats['status_counts'][status] += 1
            user_stats['type_counts'][task_type] = user_stats['type_counts'].get(task_type, 0) + 1
        
        response_data = {
            'user_stats': user_stats
        }
        
        # Add system stats for admin users
        user = db.session.get(User, user_id)
        if user and user.is_admin:
            system_stats = task_service.get_stats()
            response_data['system_stats'] = system_stats
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = f"Failed to retrieve task stats for user {user_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "user_id": user_id,
            "operation": "get_task_stats"
        })
        return jsonify({'error': 'Failed to retrieve task statistics'}), 500

@tasks_bp.route('/contexts/<int:context_id>/tasks', methods=['GET'])
@jwt_required()
def get_context_tasks(context_id: int):
    """
    Get tasks for a specific context
    
    Retrieves all tasks associated with a specific context, useful for
    tracking context-related operations.
    
    Authentication:
        Requires valid JWT token and context ownership
        
    Returns:
        200: Context tasks retrieved successfully
        403: Context not found or access denied
        500: Server error
    """
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Validate context ownership
    if not validate_context_ownership(context_id, user_id):
        logger.warning(f"Unauthorized context tasks access for context {context_id} by user {user_id}")
        return jsonify({'error': 'Context not found or access denied'}), 403
    
    try:
        # Get context tasks
        context_tasks = task_service.get_context_tasks(context_id)
        
        response_data = {
            'context_id': context_id,
            'tasks': context_tasks,
            'total_tasks': len(context_tasks)
        }
        
        logger.debug(f"Retrieved {len(context_tasks)} tasks for context {context_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = f"Failed to retrieve tasks for context {context_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "context_id": context_id,
            "user_id": user_id,
            "operation": "get_context_tasks"
        })
        return jsonify({'error': 'Failed to retrieve context tasks'}), 500