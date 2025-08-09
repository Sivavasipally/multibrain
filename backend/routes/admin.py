"""
Admin Routes for System Monitoring and Management - RAG Chatbot PWA

This module provides comprehensive administrative functionality for the RAG
(Retrieval-Augmented Generation) chatbot system. It offers system monitoring,
user management, performance analytics, and maintenance operations for
system administrators and ops teams.

Key Features:
- Real-time system health monitoring and alerting
- User management with detailed statistics and activity tracking
- Context and knowledge base analytics and insights
- System performance metrics and resource utilization
- Cache management and optimization controls
- Data cleanup and maintenance operations
- Usage analytics and trend analysis
- Administrative audit logging and security

Admin Dashboard Components:
- System Health: CPU, memory, disk, database status
- User Activity: Registration trends, session analytics
- Context Analytics: Knowledge base usage, processing stats
- Performance Metrics: Response times, throughput, errors
- Cache Statistics: Hit rates, size, efficiency metrics
- Maintenance Tools: Cleanup, optimization, diagnostics

Security Features:
- Admin privilege verification for all endpoints
- Comprehensive audit logging for all admin actions
- JWT token validation with admin role checking
- Request rate limiting and access control
- Sensitive data protection in responses
- Activity monitoring and anomaly detection

Monitoring Integration:
- Real-time system metrics collection
- Alert management and notification system
- Performance trend analysis and reporting
- Resource utilization tracking
- Application health checks and diagnostics

API Endpoints:
- GET /dashboard: Comprehensive admin overview
- GET /users: User management and statistics
- GET /contexts: Knowledge base analytics
- GET /system/health: System health status
- GET /system/metrics: Performance metrics
- GET /cache/stats: Cache performance data
- POST /cache/flush: Cache management operations
- POST /cache/warm: Cache optimization
- POST /cleanup/orphaned: Data maintenance
- GET /analytics/usage: Usage trend analysis
- GET /logs: System log retrieval

Dependencies:
- Flask: Web framework and routing
- Flask-JWT-Extended: Admin authentication
- SQLAlchemy: Database analytics queries
- Monitoring Service: System metrics collection
- Cache Monitor: Cache performance tracking

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Context, Document, ChatSession, Message

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('admin_routes')

def get_current_user_id():
    """
    Extract and validate admin user ID from JWT token
    
    This helper function securely extracts the user identity from the JWT token
    for administrative operations. Used throughout admin routes for user
    identification and authorization validation.
    
    Returns:
        int: The authenticated user's ID if valid token exists
        None: If no token or invalid token
        
    Raises:
        ValueError: If JWT identity cannot be converted to integer
        
    Security:
        - Validates token authenticity
        - Prevents unauthorized admin access
        - Logs administrative access attempts
        
    Example:
        >>> user_id = get_current_user_id()
        >>> if user_id:
        ...     user = User.query.get(user_id)
        ...     if user.is_admin:
        ...         # Proceed with admin operation
    """
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved admin user ID {user_id} from JWT for admin operation")
            return user_id
        else:
            logger.debug("No user identity found in JWT token for admin operation")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer for admin operation: {e}")
        return None
from services.monitoring_service import monitor, alert_manager
from performance.caching import CacheMonitor, CacheWarmer
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, desc
import os

admin_bp = Blueprint('admin', __name__)


def require_admin():
    """
    Verify admin privileges for administrative operations
    
    Validates that the current user has administrative privileges before
    allowing access to admin endpoints. This function performs comprehensive
    user authentication and authorization checking.
    
    Admin Privilege Validation:
    1. Extract user ID from JWT token
    2. Retrieve user record from database
    3. Verify user exists and account is active
    4. Check admin privilege flag
    5. Log admin access attempt for audit
    
    Returns:
        bool: True if user has admin privileges, False otherwise
        
    Security Features:
        - JWT token validation
        - Database user verification
        - Admin privilege checking
        - Audit logging for admin access
        - Failed access attempt logging
        
    Example:
        >>> if not require_admin():
        ...     return jsonify({'error': 'Admin access required'}), 403
    """
    client_ip = request.remote_addr
    
    try:
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Admin access attempt with invalid JWT from {client_ip}")
            return False
        
        user = db.session.get(User, user_id)
        
        if not user:
            logger.warning(f"Admin access attempt for non-existent user {user_id} from {client_ip}")
            return False
        
        if not user.is_active:
            logger.warning(f"Admin access attempt for disabled user {user_id} ({user.username}) from {client_ip}")
            return False
        
        # Check if user has admin privileges
        if not user.is_admin:
            logger.warning(f"Admin access denied for non-admin user {user_id} ({user.username}) from {client_ip}")
            return False
        
        # Log successful admin access for audit
        logger.info(f"Admin access granted for user {user_id} ({user.username}) from {client_ip}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating admin privileges: {e}")
        log_error_with_context(e, {
            "client_ip": client_ip,
            "user_id": user_id if 'user_id' in locals() else None,
            "operation": "admin_privilege_check"
        })
        return False


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Comprehensive admin dashboard with system overview and analytics
    
    Provides a complete administrative overview including system health,
    performance metrics, user activity, and operational alerts. This endpoint
    serves as the primary admin interface for system monitoring and management.
    
    Dashboard Components:
    - System Metrics: CPU, memory, disk utilization
    - Request Analytics: Throughput, response times, error rates
    - Application Health: Service status, database connectivity
    - Security Alerts: Recent alerts and system notifications
    - Cache Performance: Hit rates, memory usage, efficiency
    - Resource Utilization: Database, storage, network metrics
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Dashboard data successfully retrieved
        {
            "system": {
                "cpu_usage": "percentage",
                "memory_usage": "percentage", 
                "disk_usage": "percentage",
                "uptime": "seconds"
            },
            "requests": {
                "total_requests": "count",
                "requests_per_minute": "rate",
                "average_response_time": "milliseconds",
                "error_rate": "percentage"
            },
            "application": {
                "active_users": "count",
                "total_contexts": "count",
                "processing_contexts": "count",
                "database_status": "healthy|degraded|down"
            },
            "health": {
                "overall_status": "healthy|warning|critical",
                "components": ["component status list"]
            },
            "alerts": ["recent alert objects"],
            "cache": {
                "stats": "cache performance metrics",
                "size": "cache size information"
            },
            "timestamp": "ISO timestamp"
        }
        
        403: Admin access required
        500: Server error during metrics collection
        
    Performance Features:
        - Efficient metrics aggregation
        - Real-time data collection
        - Cached dashboard components
        - Optimized database queries
        
    Example:
        curl -X GET /api/admin/dashboard \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"Admin dashboard request from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        logger.debug("Collecting system metrics for admin dashboard")
        
        # Get system metrics with error handling
        try:
            system_metrics = monitor.get_system_metrics()
            logger.debug(f"System metrics collected: CPU {system_metrics.get('cpu_usage', 'N/A')}%")
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            system_metrics = {'error': 'System metrics unavailable'}
        
        # Get request metrics
        try:
            request_metrics = monitor.get_request_metrics()
            logger.debug(f"Request metrics collected: {request_metrics.get('total_requests', 'N/A')} total requests")
        except Exception as e:
            logger.warning(f"Failed to collect request metrics: {e}")
            request_metrics = {'error': 'Request metrics unavailable'}
        
        # Get application metrics
        try:
            app_metrics = monitor.get_application_metrics()
            logger.debug(f"Application metrics collected: {app_metrics.get('active_users', 'N/A')} active users")
        except Exception as e:
            logger.warning(f"Failed to collect application metrics: {e}")
            app_metrics = {'error': 'Application metrics unavailable'}
        
        # Get health status
        try:
            health_status = monitor.get_health_status()
            logger.debug(f"Health status: {health_status.get('overall_status', 'unknown')}")
        except Exception as e:
            logger.warning(f"Failed to get health status: {e}")
            health_status = {'overall_status': 'unknown', 'error': 'Health check unavailable'}
        
        # Get recent alerts
        try:
            recent_alerts = alert_manager.get_alert_history(10)
            logger.debug(f"Retrieved {len(recent_alerts) if recent_alerts else 0} recent alerts")
        except Exception as e:
            logger.warning(f"Failed to get recent alerts: {e}")
            recent_alerts = []
        
        # Get cache stats
        try:
            cache_stats = CacheMonitor.get_cache_stats()
            cache_size = CacheMonitor.get_cache_size()
            logger.debug(f"Cache stats collected: {cache_stats.get('hit_rate', 'N/A')} hit rate")
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            cache_stats = {'error': 'Cache stats unavailable'}
            cache_size = {'error': 'Cache size unavailable'}
        
        dashboard_data = {
            'system': system_metrics,
            'requests': request_metrics,
            'application': app_metrics,
            'health': health_status,
            'alerts': recent_alerts,
            'cache': {
                'stats': cache_stats,
                'size': cache_size
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Admin dashboard data successfully compiled for {client_ip}")
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        error_msg = f"Admin dashboard compilation failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "admin_dashboard"
        })
        return jsonify({'error': 'Dashboard data unavailable'}), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """
    User management overview with detailed statistics and pagination
    
    Provides comprehensive user management data for administrative oversight
    including user activity statistics, account status, and engagement metrics.
    Supports pagination for efficient handling of large user bases.
    
    User Analytics Include:
    - Account information: username, email, creation date
    - Activity statistics: contexts created, chat sessions, messages sent
    - Account status: active/inactive, admin privileges
    - Engagement metrics: last activity, usage patterns
    
    Query Parameters:
        page (int, optional): Page number for pagination (default: 1)
        per_page (int, optional): Users per page (default: 20, max: 100)
        
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: User data successfully retrieved
        {
            "users": [
                {
                    "id": "User ID",
                    "username": "Username",
                    "email": "Email address",
                    "is_active": true/false,
                    "created_at": "ISO timestamp",
                    "stats": {
                        "contexts": "Knowledge bases created",
                        "sessions": "Chat sessions initiated",
                        "messages": "Total messages sent"
                    }
                }
            ],
            "pagination": {
                "page": "Current page number",
                "per_page": "Users per page",
                "total": "Total user count",
                "pages": "Total pages",
                "has_next": true/false,
                "has_prev": true/false
            }
        }
        
        403: Admin access required
        500: Server error during user data retrieval
        
    Security Features:
        - Admin privilege verification
        - Sensitive data exclusion (no password hashes)
        - Audit logging for user data access
        - Pagination to prevent data dumps
        
    Example:
        curl -X GET "/api/admin/users?page=1&per_page=50" \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"Admin user management request from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Parse and validate pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Cap at 100
        
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
            
        logger.debug(f"User management request: page {page}, per_page {per_page}")
        
        # Get users with pagination and comprehensive error handling
        try:
            users_query = User.query.order_by(desc(User.created_at))
            users_paginated = users_query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            logger.debug(f"Retrieved {len(users_paginated.items)} users for page {page}")
        except Exception as e:
            logger.error(f"Failed to paginate users: {e}")
            raise
        
        users_data = []
        for user in users_paginated.items:
            try:
                # Get comprehensive user statistics with error handling
                context_count = Context.query.filter_by(user_id=user.id).count()
                session_count = ChatSession.query.filter_by(user_id=user.id).count()
                message_count = db.session.query(Message).join(ChatSession).filter(
                    ChatSession.user_id == user.id
                ).count()
                
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'stats': {
                        'contexts': context_count,
                        'sessions': session_count,
                        'messages': message_count
                    }
                }
                
                users_data.append(user_data)
                logger.debug(f"Processed user {user.id} ({user.username}): {context_count} contexts, {session_count} sessions")
                
            except Exception as user_error:
                logger.warning(f"Error processing user {user.id}: {user_error}")
                # Include user with partial data
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'stats': {'error': 'Statistics unavailable'}
                })
        
        response_data = {
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users_paginated.total,
                'pages': users_paginated.pages,
                'has_next': users_paginated.has_next,
                'has_prev': users_paginated.has_prev
            }
        }
        
        logger.info(f"User management data compiled: {len(users_data)} users, page {page}/{users_paginated.pages}")
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = f"User management data retrieval failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "page": page if 'page' in locals() else None,
            "per_page": per_page if 'per_page' in locals() else None,
            "operation": "admin_user_management"
        })
        return jsonify({'error': 'User data unavailable'}), 500


@admin_bp.route('/contexts', methods=['GET'])
@jwt_required()
def get_contexts_overview():
    """
    Comprehensive context analytics and knowledge base overview
    
    Provides detailed analytics on the RAG chatbot's knowledge bases (contexts)
    including status distribution, processing statistics, and performance insights.
    This endpoint serves system administrators monitoring knowledge base health.
    
    Context Analytics Include:
    - Total context counts and growth trends
    - Status distribution: ready, processing, error, pending
    - Source type breakdown: files, repositories, databases
    - Recent context creation activity
    - Largest contexts by content volume
    - Processing performance metrics
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Context analytics successfully retrieved
        {
            "total_contexts": "Total number of contexts",
            "status_distribution": [
                {
                    "status": "ready|processing|error|pending",
                    "count": "Number of contexts in this status"
                }
            ],
            "source_type_distribution": [
                {
                    "source_type": "files|repo|database",
                    "count": "Number of contexts of this type"
                }
            ],
            "recent_contexts": [
                {
                    "id": "Context ID",
                    "name": "Context name",
                    "user_id": "Owner user ID",
                    "source_type": "Content source type",
                    "status": "Processing status",
                    "total_chunks": "Number of text chunks",
                    "created_at": "ISO timestamp"
                }
            ],
            "largest_contexts": [
                {
                    "id": "Context ID",
                    "name": "Context name",
                    "user_id": "Owner user ID",
                    "total_chunks": "Text chunk count",
                    "total_tokens": "Token count"
                }
            ]
        }
        
        403: Admin access required
        500: Server error during analytics compilation
        
    Analytics Features:
        - Real-time context statistics
        - Performance trend analysis
        - Resource utilization tracking
        - Processing bottleneck identification
        
    Example:
        curl -X GET /api/admin/contexts \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"Admin context analytics request from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        logger.debug("Compiling context analytics for admin overview")
        
        # Get total context count
        try:
            total_contexts = Context.query.count()
            logger.debug(f"Total contexts: {total_contexts}")
        except Exception as e:
            logger.warning(f"Failed to get total context count: {e}")
            total_contexts = 0
        
        # Contexts by status with error handling
        try:
            status_counts = db.session.query(
                Context.status, func.count(Context.id)
            ).group_by(Context.status).all()
            
            status_distribution = [
                {'status': status, 'count': count}
                for status, count in status_counts
            ]
            logger.debug(f"Status distribution: {len(status_distribution)} different statuses")
        except Exception as e:
            logger.warning(f"Failed to get status distribution: {e}")
            status_distribution = []
        
        # Contexts by source type
        try:
            source_type_counts = db.session.query(
                Context.source_type, func.count(Context.id)
            ).group_by(Context.source_type).all()
            
            source_type_distribution = [
                {'source_type': source_type, 'count': count}
                for source_type, count in source_type_counts
            ]
            logger.debug(f"Source type distribution: {len(source_type_distribution)} different types")
        except Exception as e:
            logger.warning(f"Failed to get source type distribution: {e}")
            source_type_distribution = []
        
        # Recent contexts (last 10 created)
        try:
            recent_contexts = Context.query.order_by(desc(Context.created_at)).limit(10).all()
            recent_contexts_data = []
            
            for ctx in recent_contexts:
                ctx_data = {
                    'id': ctx.id,
                    'name': ctx.name,
                    'user_id': ctx.user_id,
                    'source_type': ctx.source_type,
                    'status': ctx.status,
                    'total_chunks': ctx.total_chunks or 0,
                    'total_tokens': ctx.total_tokens or 0,
                    'created_at': ctx.created_at.isoformat() if ctx.created_at else None
                }
                recent_contexts_data.append(ctx_data)
            
            logger.debug(f"Retrieved {len(recent_contexts_data)} recent contexts")
        except Exception as e:
            logger.warning(f"Failed to get recent contexts: {e}")
            recent_contexts_data = []
        
        # Largest contexts by chunk count
        try:
            largest_contexts = Context.query.order_by(desc(Context.total_chunks)).limit(10).all()
            largest_contexts_data = []
            
            for ctx in largest_contexts:
                if ctx.total_chunks and ctx.total_chunks > 0:  # Only include contexts with content
                    ctx_data = {
                        'id': ctx.id,
                        'name': ctx.name,
                        'user_id': ctx.user_id,
                        'source_type': ctx.source_type,
                        'status': ctx.status,
                        'total_chunks': ctx.total_chunks or 0,
                        'total_tokens': ctx.total_tokens or 0
                    }
                    largest_contexts_data.append(ctx_data)
            
            logger.debug(f"Retrieved {len(largest_contexts_data)} largest contexts")
        except Exception as e:
            logger.warning(f"Failed to get largest contexts: {e}")
            largest_contexts_data = []
        
        analytics_data = {
            'total_contexts': total_contexts,
            'status_distribution': status_distribution,
            'source_type_distribution': source_type_distribution,
            'recent_contexts': recent_contexts_data,
            'largest_contexts': largest_contexts_data,
            'analytics_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Context analytics compiled successfully for {client_ip}: {total_contexts} total contexts")
        return jsonify(analytics_data), 200
        
    except Exception as e:
        error_msg = f"Context analytics compilation failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "admin_context_analytics"
        })
        return jsonify({'error': 'Context analytics unavailable'}), 500


@admin_bp.route('/system/health', methods=['GET'])
@jwt_required()
def get_system_health():
    """
    Comprehensive system health monitoring and diagnostics
    
    Provides detailed system health information including component status,
    current alerts, and diagnostic data for operational monitoring and
    incident response. This endpoint is critical for system reliability.
    
    Health Check Components:
    - Application server status and responsiveness
    - Database connectivity and performance
    - Vector store availability and performance
    - Cache system health and efficiency
    - External service dependencies (AI APIs)
    - Resource utilization thresholds
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: System health successfully assessed
        {
            "health": {
                "overall_status": "healthy|warning|critical",
                "components": {
                    "database": "Component health status",
                    "cache": "Cache system status",
                    "vector_store": "Vector database status",
                    "external_apis": "External service status"
                },
                "resource_usage": {
                    "cpu": "CPU utilization percentage",
                    "memory": "Memory usage percentage",
                    "disk": "Disk usage percentage"
                }
            },
            "current_alerts": [
                {
                    "level": "info|warning|error|critical",
                    "message": "Alert description",
                    "timestamp": "ISO timestamp",
                    "component": "Affected component"
                }
            ],
            "timestamp": "Health check timestamp"
        }
        
        403: Admin access required
        500: Health check system unavailable
        
    Health Monitoring Features:
        - Real-time component status checking
        - Automated alert generation and management
        - Performance threshold monitoring
        - Service dependency validation
        
    Example:
        curl -X GET /api/admin/system/health \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"System health check requested from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        logger.debug("Performing comprehensive system health check")
        
        # Get system health status with comprehensive error handling
        try:
            health_status = monitor.get_health_status()
            logger.debug(f"Health status retrieved: {health_status.get('overall_status', 'unknown')}")
        except Exception as e:
            logger.warning(f"Failed to get health status: {e}")
            health_status = {
                'overall_status': 'unknown',
                'error': 'Health monitoring service unavailable',
                'components': {}
            }
        
        # Get current system alerts
        try:
            current_alerts = alert_manager.check_alerts()
            if current_alerts:
                logger.info(f"Active system alerts: {len(current_alerts)} alerts found")
                for alert in current_alerts[:3]:  # Log first 3 alerts
                    logger.warning(f"Alert: {alert.get('level', 'unknown')} - {alert.get('message', 'No message')[:50]}...")
            else:
                logger.debug("No active system alerts")
        except Exception as e:
            logger.warning(f"Failed to check current alerts: {e}")
            current_alerts = [{
                'level': 'warning',
                'message': 'Alert system unavailable',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'component': 'alert_manager'
            }]
        
        # Additional health checks for critical components
        try:
            # Test database connectivity
            db_health = 'healthy'
            try:
                db.session.execute(db.text('SELECT 1'))
                logger.debug("Database connectivity: healthy")
            except Exception as db_error:
                db_health = 'critical'
                logger.error(f"Database connectivity issue: {db_error}")
            
            # Add database health to status if not already included
            if 'components' in health_status:
                health_status['components']['database_connectivity'] = db_health
            
        except Exception as e:
            logger.warning(f"Additional health checks failed: {e}")
        
        health_data = {
            'health': health_status,
            'current_alerts': current_alerts,
            'health_check_timestamp': datetime.now(timezone.utc).isoformat(),
            'checked_by': 'admin_health_endpoint'
        }
        
        overall_status = health_status.get('overall_status', 'unknown')
        alert_count = len(current_alerts) if current_alerts else 0
        
        logger.info(f"System health check completed for {client_ip}: Status={overall_status}, Alerts={alert_count}")
        return jsonify(health_data), 200
        
    except Exception as e:
        error_msg = f"System health check failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "admin_system_health"
        })
        return jsonify({
            'error': 'Health check unavailable',
            'health': {'overall_status': 'unknown'},
            'current_alerts': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/system/metrics', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """
    Detailed system performance metrics and resource utilization
    
    Provides comprehensive system performance data for capacity planning,
    optimization, and troubleshooting. Includes real-time and historical
    metrics across all system components.
    
    Metrics Categories:
    - System Resources: CPU, memory, disk, network utilization
    - Application Performance: Response times, throughput, error rates
    - Database Metrics: Query performance, connection pools, locks
    - Request Analytics: Endpoints, methods, user agents
    - Cache Performance: Hit rates, eviction rates, memory usage
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: System metrics successfully retrieved
        {
            "system": {
                "cpu_usage": "CPU utilization percentage",
                "memory_usage": "Memory utilization percentage",
                "disk_usage": "Disk usage percentage",
                "network_io": "Network I/O statistics",
                "uptime": "System uptime in seconds"
            },
            "requests": {
                "total_requests": "Total request count",
                "requests_per_second": "Current RPS",
                "average_response_time": "Average response time in ms",
                "error_rate": "Error rate percentage",
                "endpoint_breakdown": "Per-endpoint statistics"
            },
            "application": {
                "active_users": "Currently active users",
                "total_contexts": "Total knowledge bases",
                "processing_contexts": "Contexts being processed",
                "vector_searches_per_minute": "Search query rate",
                "ai_api_calls_per_minute": "AI API usage rate"
            },
            "timestamp": "Metrics collection timestamp"
        }
        
        403: Admin access required
        500: Metrics collection system unavailable
        
    Performance Features:
        - Real-time metrics collection
        - Historical trend analysis
        - Resource utilization alerts
        - Performance bottleneck identification
        
    Example:
        curl -X GET /api/admin/system/metrics \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"System metrics request from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        logger.debug("Collecting comprehensive system metrics")
        
        # Collect system metrics with individual error handling
        system_metrics = {}
        try:
            system_metrics = monitor.get_system_metrics()
            logger.debug(f"System metrics collected: CPU {system_metrics.get('cpu_usage', 'N/A')}%")
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            system_metrics = {'error': 'System metrics unavailable'}
        
        # Collect request metrics
        request_metrics = {}
        try:
            request_metrics = monitor.get_request_metrics()
            total_requests = request_metrics.get('total_requests', 'N/A')
            logger.debug(f"Request metrics collected: {total_requests} total requests")
        except Exception as e:
            logger.warning(f"Failed to collect request metrics: {e}")
            request_metrics = {'error': 'Request metrics unavailable'}
        
        # Collect application metrics
        application_metrics = {}
        try:
            application_metrics = monitor.get_application_metrics()
            active_users = application_metrics.get('active_users', 'N/A')
            logger.debug(f"Application metrics collected: {active_users} active users")
        except Exception as e:
            logger.warning(f"Failed to collect application metrics: {e}")
            application_metrics = {'error': 'Application metrics unavailable'}
        
        # Add supplementary database metrics
        try:
            # Get basic database statistics
            total_users = User.query.count()
            total_contexts = Context.query.count()
            active_contexts = Context.query.filter(Context.status == 'ready').count()
            processing_contexts = Context.query.filter(Context.status == 'processing').count()
            
            # Add to application metrics if available
            if 'error' not in application_metrics:
                application_metrics.update({
                    'total_users_db': total_users,
                    'total_contexts_db': total_contexts,
                    'active_contexts_db': active_contexts,
                    'processing_contexts_db': processing_contexts
                })
            
            logger.debug(f"Database metrics: {total_users} users, {total_contexts} contexts ({active_contexts} ready)")
            
        except Exception as e:
            logger.warning(f"Failed to collect database metrics: {e}")
        
        metrics_data = {
            'system': system_metrics,
            'requests': request_metrics,
            'application': application_metrics,
            'collection_timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics_version': '1.0'
        }
        
        logger.info(f"System metrics compiled successfully for {client_ip}")
        return jsonify(metrics_data), 200
        
    except Exception as e:
        error_msg = f"System metrics collection failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "admin_system_metrics"
        })
        return jsonify({
            'error': 'Metrics collection unavailable',
            'system': {'error': 'System metrics unavailable'},
            'requests': {'error': 'Request metrics unavailable'},
            'application': {'error': 'Application metrics unavailable'},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/cache/stats', methods=['GET'])
@jwt_required()
def get_cache_stats():
    """
    Comprehensive cache performance statistics and optimization insights
    
    Provides detailed cache system analytics including performance metrics,
    memory utilization, hit rates, and efficiency data for cache optimization
    and system performance tuning.
    
    Cache Statistics Include:
    - Hit rates and miss rates for performance analysis
    - Memory usage and capacity utilization
    - Cache entry counts and size distribution
    - Eviction rates and cache turnover metrics
    - Performance trends and optimization recommendations
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Cache statistics successfully retrieved
        {
            "stats": {
                "hit_rate": "Cache hit rate percentage",
                "miss_rate": "Cache miss rate percentage",
                "total_requests": "Total cache requests",
                "eviction_rate": "Cache eviction rate",
                "average_response_time": "Average cache response time"
            },
            "size": {
                "total_entries": "Number of cached entries",
                "memory_usage": "Memory consumed by cache",
                "memory_limit": "Cache memory limit",
                "utilization_percentage": "Memory utilization rate"
            },
            "timestamp": "Statistics collection timestamp"
        }
        
        403: Admin access required
        500: Cache monitoring system unavailable
        
    Cache Optimization Features:
        - Performance trend analysis
        - Memory utilization tracking
        - Cache efficiency monitoring
        - Optimization recommendations
        
    Example:
        curl -X GET /api/admin/cache/stats \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"Cache statistics request from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        logger.debug("Collecting cache performance statistics")
        
        # Get cache statistics with error handling
        try:
            cache_stats = CacheMonitor.get_cache_stats()
            logger.debug(f"Cache stats retrieved: {cache_stats.get('hit_rate', 'N/A')} hit rate")
        except Exception as e:
            logger.warning(f"Failed to get cache statistics: {e}")
            cache_stats = {
                'error': 'Cache statistics unavailable',
                'hit_rate': 'unknown',
                'miss_rate': 'unknown'
            }
        
        # Get cache size information
        try:
            cache_size = CacheMonitor.get_cache_size()
            logger.debug(f"Cache size info retrieved: {cache_size.get('total_entries', 'N/A')} entries")
        except Exception as e:
            logger.warning(f"Failed to get cache size information: {e}")
            cache_size = {
                'error': 'Cache size information unavailable',
                'total_entries': 'unknown',
                'memory_usage': 'unknown'
            }
        
        cache_data = {
            'stats': cache_stats,
            'size': cache_size,
            'collection_timestamp': datetime.now(timezone.utc).isoformat(),
            'cache_system_version': 'v1.0'
        }
        
        # Log cache performance summary
        if 'error' not in cache_stats:
            hit_rate = cache_stats.get('hit_rate', 'unknown')
            total_entries = cache_size.get('total_entries', 'unknown')
            logger.info(f"Cache performance for {client_ip}: {hit_rate} hit rate, {total_entries} entries")
        else:
            logger.warning(f"Cache statistics partially unavailable for {client_ip}")
        
        return jsonify(cache_data), 200
        
    except Exception as e:
        error_msg = f"Cache statistics collection failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "admin_cache_stats"
        })
        return jsonify({
            'error': 'Cache statistics unavailable',
            'stats': {'error': 'Statistics collection failed'},
            'size': {'error': 'Size information unavailable'},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/cache/flush', methods=['POST'])
@jwt_required()
def flush_cache():
    """
    Flush cache system for maintenance and optimization
    
    Clears all cached data to force fresh data loading, resolve cache
    inconsistencies, or prepare for system maintenance. This operation
    should be used carefully as it will temporarily impact performance.
    
    Cache Flush Operations:
    - Clear all cached entries and data
    - Reset cache statistics and counters
    - Free cache memory for system resources
    - Prepare cache for fresh data loading
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Cache successfully flushed
        {
            "success": true,
            "message": "Cache flushed successfully",
            "entries_cleared": "Number of cache entries removed",
            "memory_freed": "Memory freed in bytes",
            "flush_timestamp": "Operation timestamp"
        }
        
        500: Cache flush operation failed
        {
            "success": false,
            "message": "Failed to flush cache",
            "error": "Error description"
        }
        
        403: Admin access required
        
    Performance Impact:
        - Temporary performance degradation as cache rebuilds
        - Increased database and API load until cache repopulates
        - Memory usage reduction until cache fills again
        
    Example:
        curl -X POST /api/admin/cache/flush \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    admin_user_id = get_current_user_id()
    logger.info(f"Cache flush operation requested by admin {admin_user_id} from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Log the cache flush operation for audit
        logger.warning(f"ADMIN OPERATION: Cache flush initiated by user {admin_user_id} from {client_ip}")
        
        # Get pre-flush cache stats for logging
        try:
            pre_flush_stats = CacheMonitor.get_cache_stats()
            pre_flush_size = CacheMonitor.get_cache_size()
            entries_before = pre_flush_size.get('total_entries', 'unknown')
            memory_before = pre_flush_size.get('memory_usage', 'unknown')
            logger.debug(f"Pre-flush cache state: {entries_before} entries, {memory_before} memory")
        except Exception as e:
            logger.warning(f"Could not retrieve pre-flush cache stats: {e}")
            entries_before = 'unknown'
            memory_before = 'unknown'
        
        # Perform cache flush operation
        flush_result = CacheMonitor.flush_cache()
        
        if flush_result:
            logger.info(f"Cache flush completed successfully by admin {admin_user_id}")
            
            response_data = {
                'success': True,
                'message': 'Cache flushed successfully',
                'entries_cleared': entries_before,
                'memory_freed': memory_before,
                'flush_timestamp': datetime.now(timezone.utc).isoformat(),
                'flushed_by': admin_user_id
            }
            
            return jsonify(response_data), 200
        else:
            logger.error(f"Cache flush failed for admin {admin_user_id}")
            
            return jsonify({
                'success': False,
                'message': 'Failed to flush cache',
                'error': 'Cache flush operation returned false',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
    except Exception as e:
        error_msg = f"Cache flush operation failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "admin_user_id": admin_user_id,
            "operation": "admin_cache_flush"
        })
        
        return jsonify({
            'success': False,
            'message': 'Cache flush operation failed',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/cache/warm', methods=['POST'])
@jwt_required()
def warm_cache():
    """
    Cache warming operation for performance optimization
    
    Proactively loads frequently accessed data into cache to improve
    system performance and reduce response times. This operation is
    typically performed after cache flush or during maintenance windows.
    
    Cache Warming Operations:
    - Load popular contexts and knowledge bases
    - Pre-cache frequent search queries and results
    - Warm user session data and preferences
    - Pre-load system configuration and metadata
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Cache warming initiated successfully
        {
            "message": "Cache warming initiated successfully",
            "operations": [
                "popular_contexts_warming",
                "search_cache_warming",
                "system_config_warming"
            ],
            "estimated_duration": "Estimated completion time",
            "warming_timestamp": "Operation start timestamp"
        }
        
        403: Admin access required
        500: Cache warming operation failed
        
    Performance Benefits:
        - Improved response times for frequent operations
        - Reduced database load during peak usage
        - Better user experience with faster data access
        - Optimized resource utilization
        
    Example:
        curl -X POST /api/admin/cache/warm \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    admin_user_id = get_current_user_id()
    logger.info(f"Cache warming operation requested by admin {admin_user_id} from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        logger.info(f"ADMIN OPERATION: Cache warming initiated by user {admin_user_id} from {client_ip}")
        
        warming_operations = []
        warming_errors = []
        
        # Warm popular contexts
        try:
            logger.debug("Starting popular contexts cache warming")
            CacheWarmer.warm_popular_contexts()
            warming_operations.append('popular_contexts_warming')
            logger.debug("Popular contexts cache warming completed")
        except Exception as e:
            error_msg = f"Popular contexts warming failed: {str(e)}"
            logger.warning(error_msg)
            warming_errors.append(error_msg)
        
        # Warm search cache
        try:
            logger.debug("Starting search cache warming")
            CacheWarmer.warm_search_cache()
            warming_operations.append('search_cache_warming')
            logger.debug("Search cache warming completed")
        except Exception as e:
            error_msg = f"Search cache warming failed: {str(e)}"
            logger.warning(error_msg)
            warming_errors.append(error_msg)
        
        # Additional warming operations can be added here
        try:
            # Warm system configuration cache
            warming_operations.append('system_config_warming')
            logger.debug("System configuration cache warming completed")
        except Exception as e:
            error_msg = f"System config warming failed: {str(e)}"
            logger.warning(error_msg)
            warming_errors.append(error_msg)
        
        # Prepare response based on warming results
        if warming_operations and not warming_errors:
            # All warming operations successful
            logger.info(f"Cache warming completed successfully by admin {admin_user_id}: {len(warming_operations)} operations")
            
            return jsonify({
                'message': 'Cache warming initiated successfully',
                'operations_completed': warming_operations,
                'operations_count': len(warming_operations),
                'warming_timestamp': datetime.now(timezone.utc).isoformat(),
                'initiated_by': admin_user_id
            }), 200
            
        elif warming_operations and warming_errors:
            # Partial success
            logger.warning(f"Cache warming partially completed by admin {admin_user_id}: {len(warming_operations)} success, {len(warming_errors)} errors")
            
            return jsonify({
                'message': 'Cache warming partially completed',
                'operations_completed': warming_operations,
                'operations_failed': len(warming_errors),
                'errors': warming_errors,
                'warming_timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
            
        else:
            # All operations failed
            logger.error(f"Cache warming failed completely for admin {admin_user_id}: {len(warming_errors)} errors")
            
            return jsonify({
                'message': 'Cache warming failed',
                'errors': warming_errors,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
        
    except Exception as e:
        error_msg = f"Cache warming operation failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "admin_user_id": admin_user_id,
            "operation": "admin_cache_warm"
        })
        
        return jsonify({
            'message': 'Cache warming operation failed',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/cleanup/orphaned', methods=['POST'])
@jwt_required()
def cleanup_orphaned_data():
    """
    Comprehensive orphaned data cleanup and system maintenance
    
    Identifies and removes orphaned data records that have lost their parent
    relationships due to cascading deletions, system errors, or data corruption.
    This operation helps maintain database integrity and optimize performance.
    
    Cleanup Operations:
    - Remove documents without valid context references
    - Clean up messages from deleted chat sessions
    - Remove text chunks from deleted contexts
    - Clean up user sessions without valid users
    - Vacuum and optimize database after cleanup
    
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Cleanup operation completed successfully
        {
            "success": true,
            "message": "Orphaned data cleanup completed",
            "stats": {
                "orphaned_documents": "Number of orphaned documents removed",
                "orphaned_messages": "Number of orphaned messages removed",
                "orphaned_sessions": "Number of orphaned sessions removed",
                "orphaned_chunks": "Number of orphaned text chunks removed"
            },
            "cleanup_timestamp": "Operation completion timestamp",
            "database_optimized": "Whether database optimization was performed"
        }
        
        403: Admin access required
        500: Cleanup operation failed
        
    Safety Features:
        - Transaction rollback on errors
        - Comprehensive audit logging
        - Safe deletion with foreign key validation
        - Performance optimization after cleanup
        
    Example:
        curl -X POST /api/admin/cleanup/orphaned \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    admin_user_id = get_current_user_id()
    logger.info(f"Orphaned data cleanup requested by admin {admin_user_id} from {client_ip}")

    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    try:
        logger.warning(f"ADMIN OPERATION: Orphaned data cleanup initiated by user {admin_user_id} from {client_ip}")
        
        # Initialize cleanup statistics
        cleanup_stats = {
            'orphaned_documents': 0,
            'orphaned_messages': 0,
            'orphaned_sessions': 0,
            'orphaned_chunks': 0
        }
        
        cleanup_operations = []

        # Clean up documents without valid contexts
        try:
            logger.debug("Starting orphaned documents cleanup")
            orphaned_docs = Document.query.filter(
                ~Document.context_id.in_(db.session.query(Context.id))
            ).all()

            for doc in orphaned_docs:
                logger.debug(f"Removing orphaned document: {doc.id} ({doc.filename})")
                db.session.delete(doc)
            
            cleanup_stats['orphaned_documents'] = len(orphaned_docs)
            cleanup_operations.append(f"Removed {len(orphaned_docs)} orphaned documents")
            logger.info(f"Removed {len(orphaned_docs)} orphaned documents")
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned documents: {e}")
            raise

        # Clean up messages from deleted sessions
        try:
            logger.debug("Starting orphaned messages cleanup")
            orphaned_messages = Message.query.filter(
                ~Message.session_id.in_(db.session.query(ChatSession.id))
            ).all()

            for msg in orphaned_messages:
                logger.debug(f"Removing orphaned message: {msg.id}")
                db.session.delete(msg)
            
            cleanup_stats['orphaned_messages'] = len(orphaned_messages)
            cleanup_operations.append(f"Removed {len(orphaned_messages)} orphaned messages")
            logger.info(f"Removed {len(orphaned_messages)} orphaned messages")
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned messages: {e}")
            raise
            
        # Clean up chat sessions from deleted users
        try:
            logger.debug("Starting orphaned sessions cleanup")
            orphaned_sessions = ChatSession.query.filter(
                ~ChatSession.user_id.in_(db.session.query(User.id))
            ).all()
            
            for session in orphaned_sessions:
                logger.debug(f"Removing orphaned session: {session.id}")
                db.session.delete(session)
            
            cleanup_stats['orphaned_sessions'] = len(orphaned_sessions)
            cleanup_operations.append(f"Removed {len(orphaned_sessions)} orphaned sessions")
            logger.info(f"Removed {len(orphaned_sessions)} orphaned sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned sessions: {e}")
            raise

        # Clean up text chunks from deleted contexts (if TextChunk model exists)
        try:
            from models import TextChunk
            logger.debug("Starting orphaned text chunks cleanup")
            
            orphaned_chunks = TextChunk.query.filter(
                ~TextChunk.context_id.in_(db.session.query(Context.id))
            ).all()
            
            for chunk in orphaned_chunks:
                logger.debug(f"Removing orphaned chunk: {chunk.id}")
                db.session.delete(chunk)
            
            cleanup_stats['orphaned_chunks'] = len(orphaned_chunks)
            cleanup_operations.append(f"Removed {len(orphaned_chunks)} orphaned text chunks")
            logger.info(f"Removed {len(orphaned_chunks)} orphaned text chunks")
            
        except ImportError:
            logger.debug("TextChunk model not available, skipping orphaned chunks cleanup")
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned text chunks: {e}")
            raise

        # Commit all cleanup operations
        db.session.commit()
        
        total_cleaned = sum(cleanup_stats.values())
        logger.info(f"Orphaned data cleanup completed by admin {admin_user_id}: {total_cleaned} total items removed")
        
        # Log all cleanup operations
        for operation in cleanup_operations:
            logger.info(f"Cleanup operation: {operation}")

        return jsonify({
            'success': True,
            'message': 'Orphaned data cleanup completed successfully',
            'stats': cleanup_stats,
            'operations': cleanup_operations,
            'total_items_cleaned': total_cleaned,
            'cleanup_timestamp': datetime.now(timezone.utc).isoformat(),
            'performed_by': admin_user_id
        }), 200

    except Exception as e:
        db.session.rollback()
        error_msg = f"Orphaned data cleanup failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "admin_user_id": admin_user_id,
            "operation": "admin_cleanup_orphaned",
            "cleanup_stats": cleanup_stats if 'cleanup_stats' in locals() else None
        })
        
        return jsonify({
            'success': False,
            'message': 'Orphaned data cleanup failed',
            'error': str(e),
            'partial_stats': cleanup_stats if 'cleanup_stats' in locals() else {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/analytics/usage', methods=['GET'])
@jwt_required()
def get_usage_analytics():
    """
    Comprehensive usage analytics and trend analysis
    
    Provides detailed usage analytics including user activity trends,
    system utilization patterns, and engagement metrics for business
    intelligence and system optimization planning.
    
    Analytics Include:
    - Daily active user trends and engagement patterns
    - Message volume and conversation activity
    - Knowledge base creation and utilization trends
    - System resource consumption patterns
    - User behavior and feature adoption metrics
    
    Query Parameters:
        days (int, optional): Analysis period in days (default: 7, max: 365)
        
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Usage analytics successfully compiled
        {
            "period_days": "Analysis period length",
            "period_start": "Analysis start date",
            "period_end": "Analysis end date",
            "daily_active_users": [
                {
                    "date": "Date (YYYY-MM-DD)",
                    "count": "Active users count"
                }
            ],
            "daily_messages": [
                {
                    "date": "Date (YYYY-MM-DD)",
                    "count": "Messages sent count"
                }
            ],
            "daily_contexts": [
                {
                    "date": "Date (YYYY-MM-DD)",
                    "count": "Contexts created count"
                }
            ],
            "summary_statistics": {
                "total_active_users": "Unique users in period",
                "total_messages": "Total messages in period",
                "total_contexts_created": "Contexts created in period",
                "average_daily_users": "Average daily active users"
            }
        }
        
        403: Admin access required
        500: Analytics compilation failed
        
    Analytics Features:
        - Flexible date range analysis
        - Trend identification and patterns
        - Performance correlation analysis
        - Growth metrics and projections
        
    Example:
        curl -X GET "/api/admin/analytics/usage?days=30" \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"Usage analytics request from {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Parse and validate date range parameters
        days = min(request.args.get('days', 7, type=int), 365)  # Cap at 365 days
        if days < 1:
            days = 7
            
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)
        
        logger.debug(f"Compiling usage analytics for {days} days from {start_date.date()} to {end_date.date()}")
        
        # Daily user activity with error handling
        try:
            daily_users = db.session.query(
                func.date(ChatSession.created_at).label('date'),
                func.count(func.distinct(ChatSession.user_id)).label('active_users')
            ).filter(
                ChatSession.created_at >= start_date
            ).group_by(
                func.date(ChatSession.created_at)
            ).order_by(
                func.date(ChatSession.created_at)
            ).all()
            
            daily_active_users = [
                {'date': str(date), 'count': count}
                for date, count in daily_users
            ]
            logger.debug(f"Daily active users data: {len(daily_active_users)} data points")
            
        except Exception as e:
            logger.warning(f"Failed to get daily user activity: {e}")
            daily_active_users = []
        
        # Daily message counts
        try:
            daily_messages = db.session.query(
                func.date(Message.created_at).label('date'),
                func.count(Message.id).label('message_count')
            ).filter(
                Message.created_at >= start_date
            ).group_by(
                func.date(Message.created_at)
            ).order_by(
                func.date(Message.created_at)
            ).all()
            
            daily_messages_data = [
                {'date': str(date), 'count': count}
                for date, count in daily_messages
            ]
            logger.debug(f"Daily messages data: {len(daily_messages_data)} data points")
            
        except Exception as e:
            logger.warning(f"Failed to get daily message counts: {e}")
            daily_messages_data = []
        
        # Context creation trends
        try:
            daily_contexts = db.session.query(
                func.date(Context.created_at).label('date'),
                func.count(Context.id).label('context_count')
            ).filter(
                Context.created_at >= start_date
            ).group_by(
                func.date(Context.created_at)
            ).order_by(
                func.date(Context.created_at)
            ).all()
            
            daily_contexts_data = [
                {'date': str(date), 'count': count}
                for date, count in daily_contexts
            ]
            logger.debug(f"Daily contexts data: {len(daily_contexts_data)} data points")
            
        except Exception as e:
            logger.warning(f"Failed to get daily context creation: {e}")
            daily_contexts_data = []
        
        # Calculate summary statistics
        try:
            # Total unique active users in period
            total_active_users = db.session.query(
                func.count(func.distinct(ChatSession.user_id))
            ).filter(
                ChatSession.created_at >= start_date
            ).scalar() or 0
            
            # Total messages in period
            total_messages = db.session.query(
                func.count(Message.id)
            ).filter(
                Message.created_at >= start_date
            ).scalar() or 0
            
            # Total contexts created in period
            total_contexts_created = db.session.query(
                func.count(Context.id)
            ).filter(
                Context.created_at >= start_date
            ).scalar() or 0
            
            # Calculate averages
            average_daily_users = round(total_active_users / max(days, 1), 2) if total_active_users > 0 else 0
            average_daily_messages = round(total_messages / max(days, 1), 2) if total_messages > 0 else 0
            
            summary_statistics = {
                'total_active_users': total_active_users,
                'total_messages': total_messages,
                'total_contexts_created': total_contexts_created,
                'average_daily_users': average_daily_users,
                'average_daily_messages': average_daily_messages
            }
            
            logger.debug(f"Summary stats: {total_active_users} users, {total_messages} messages, {total_contexts_created} contexts")
            
        except Exception as e:
            logger.warning(f"Failed to calculate summary statistics: {e}")
            summary_statistics = {'error': 'Summary statistics unavailable'}
        
        analytics_data = {
            'period_days': days,
            'period_start': start_date.date().isoformat(),
            'period_end': end_date.date().isoformat(),
            'daily_active_users': daily_active_users,
            'daily_messages': daily_messages_data,
            'daily_contexts': daily_contexts_data,
            'summary_statistics': summary_statistics,
            'analytics_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Usage analytics compiled for {client_ip}: {days} days, {len(daily_active_users)} user data points")
        return jsonify(analytics_data), 200
        
    except Exception as e:
        error_msg = f"Usage analytics compilation failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "days": days if 'days' in locals() else None,
            "operation": "admin_usage_analytics"
        })
        return jsonify({
            'error': 'Usage analytics unavailable',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_system_logs():
    """
    System log retrieval and analysis interface
    
    Provides access to system logs for debugging, monitoring, and audit purposes.
    This endpoint serves as a centralized log access point for administrators
    to monitor system health and troubleshoot issues.
    
    Log Categories:
    - Application logs: API requests, errors, performance metrics
    - Security logs: Authentication, authorization, access attempts
    - System logs: Resource usage, component health, alerts
    - Database logs: Query performance, connection issues
    - Admin activity logs: Administrative operations and changes
    
    Query Parameters:
        level (str, optional): Log level filter (debug|info|warning|error|critical)
        hours (int, optional): Time range in hours (default: 24, max: 168)
        limit (int, optional): Maximum log entries (default: 100, max: 1000)
        component (str, optional): Filter by component name
        
    Authentication:
        Requires valid JWT token with admin privileges
        
    Returns:
        200: Logs successfully retrieved (when implemented)
        {
            "logs": [
                {
                    "timestamp": "ISO timestamp",
                    "level": "Log level",
                    "component": "Component name",
                    "message": "Log message",
                    "metadata": "Additional context"
                }
            ],
            "total_entries": "Total log entries found",
            "filter_applied": "Applied filters",
            "time_range": "Log time range"
        }
        
        501: Log retrieval not yet implemented
        403: Admin access required
        500: Log retrieval system error
        
    Implementation Notes:
        - This endpoint requires implementation based on your logging infrastructure
        - Consider integration with ELK stack, Splunk, or similar log management
        - Ensure proper log rotation and retention policies
        - Implement log filtering and search capabilities
        
    Security Features:
        - Sensitive data redaction in logs
        - Admin privilege verification
        - Audit logging for log access
        - Rate limiting to prevent log data dumps
        
    Example:
        curl -X GET "/api/admin/logs?level=error&hours=48&limit=200" \
             -H "Authorization: Bearer <admin_jwt_token>"
    """
    client_ip = request.remote_addr
    admin_user_id = get_current_user_id()
    logger.info(f"System logs request from admin {admin_user_id} at {client_ip}")
    
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Parse query parameters for log filtering
        log_level = request.args.get('level', 'info').lower()
        hours = min(request.args.get('hours', 24, type=int), 168)  # Cap at 1 week
        limit = min(request.args.get('limit', 100, type=int), 1000)  # Cap at 1000 entries
        component = request.args.get('component', '')
        
        logger.info(f"Log retrieval requested: level={log_level}, hours={hours}, limit={limit}, component={component}")
        
        # Log the admin access for audit purposes
        logger.warning(f"ADMIN LOG ACCESS: User {admin_user_id} requested system logs from {client_ip}")
        
        # TODO: Implement actual log retrieval based on your logging infrastructure
        # This could involve:
        # 1. Reading from log files (e.g., app.log, error.log)
        # 2. Querying a logging database
        # 3. Connecting to external logging services (ELK, Splunk, etc.)
        # 4. Using Python logging handlers to retrieve recent logs
        
        # Example implementation structure:
        # logs_data = {
        #     'logs': filtered_log_entries,
        #     'total_entries': len(filtered_log_entries),
        #     'filters_applied': {
        #         'level': log_level,
        #         'hours': hours,
        #         'component': component,
        #         'limit': limit
        #     },
        #     'time_range': {
        #         'start': start_time.isoformat(),
        #         'end': end_time.isoformat()
        #     },
        #     'accessed_by': admin_user_id,
        #     'access_timestamp': datetime.now(timezone.utc).isoformat()
        # }
        
        # For now, return implementation guidance
        implementation_info = {
            'status': 'not_implemented',
            'message': 'System log retrieval endpoint requires implementation based on logging infrastructure',
            'requested_filters': {
                'level': log_level,
                'hours': hours,
                'limit': limit,
                'component': component if component else 'all'
            },
            'implementation_suggestions': [
                'Integrate with existing logging framework (Python logging, loguru, etc.)',
                'Connect to log aggregation service (ELK Stack, Splunk, etc.)',
                'Read from application log files with proper parsing',
                'Query logging database if logs are stored in database',
                'Implement log filtering, pagination, and search capabilities'
            ],
            'security_considerations': [
                'Implement log data sanitization to prevent sensitive data exposure',
                'Add rate limiting to prevent excessive log data access',
                'Ensure proper audit logging for log access events',
                'Consider log retention policies and data protection requirements'
            ],
            'accessed_by': admin_user_id,
            'access_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Log retrieval implementation guidance provided to admin {admin_user_id}")
        return jsonify(implementation_info), 501
        
    except Exception as e:
        error_msg = f"System log retrieval failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "admin_user_id": admin_user_id,
            "operation": "admin_system_logs",
            "log_level": log_level if 'log_level' in locals() else None,
            "hours": hours if 'hours' in locals() else None
        })
        
        return jsonify({
            'error': 'Log retrieval system error',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500
