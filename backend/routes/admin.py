"""
Admin routes for system monitoring and management
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Context, Document, ChatSession, Message
from services.monitoring_service import monitor, alert_manager
from performance.caching import CacheMonitor, CacheWarmer
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, desc
import os

admin_bp = Blueprint('admin', __name__)


def require_admin():
    """Check if current user is admin (placeholder - implement proper admin check)"""
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    # For now, allow any authenticated user
    # In production, add proper admin role checking
    if not user:
        return False
    
    # TODO: Add proper admin role checking
    # return user.is_admin or user.role == 'admin'
    return True


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get admin dashboard overview"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Get system metrics
        system_metrics = monitor.get_system_metrics()
        request_metrics = monitor.get_request_metrics()
        app_metrics = monitor.get_application_metrics()
        health_status = monitor.get_health_status()
        
        # Get recent alerts
        recent_alerts = alert_manager.get_alert_history(10)
        
        # Get cache stats
        cache_stats = CacheMonitor.get_cache_stats()
        cache_size = CacheMonitor.get_cache_size()
        
        return jsonify({
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
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get user management overview"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get users with pagination
        users_query = User.query.order_by(desc(User.created_at))
        users_paginated = users_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = []
        for user in users_paginated.items:
            # Get user statistics
            context_count = Context.query.filter_by(user_id=user.id).count()
            session_count = ChatSession.query.filter_by(user_id=user.id).count()
            message_count = db.session.query(Message).join(ChatSession).filter(
                ChatSession.user_id == user.id
            ).count()
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'stats': {
                    'contexts': context_count,
                    'sessions': session_count,
                    'messages': message_count
                }
            })
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users_paginated.total,
                'pages': users_paginated.pages,
                'has_next': users_paginated.has_next,
                'has_prev': users_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/contexts', methods=['GET'])
@jwt_required()
def get_contexts_overview():
    """Get contexts overview for admin"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Get context statistics
        total_contexts = Context.query.count()
        
        # Contexts by status
        status_counts = db.session.query(
            Context.status, func.count(Context.id)
        ).group_by(Context.status).all()
        
        # Contexts by source type
        source_type_counts = db.session.query(
            Context.source_type, func.count(Context.id)
        ).group_by(Context.source_type).all()
        
        # Recent contexts
        recent_contexts = Context.query.order_by(desc(Context.created_at)).limit(10).all()
        
        # Largest contexts by chunks
        largest_contexts = Context.query.order_by(desc(Context.total_chunks)).limit(10).all()
        
        return jsonify({
            'total_contexts': total_contexts,
            'status_distribution': [
                {'status': status, 'count': count} 
                for status, count in status_counts
            ],
            'source_type_distribution': [
                {'source_type': source_type, 'count': count} 
                for source_type, count in source_type_counts
            ],
            'recent_contexts': [
                {
                    'id': ctx.id,
                    'name': ctx.name,
                    'user_id': ctx.user_id,
                    'source_type': ctx.source_type,
                    'status': ctx.status,
                    'total_chunks': ctx.total_chunks,
                    'created_at': ctx.created_at.isoformat() if ctx.created_at else None
                }
                for ctx in recent_contexts
            ],
            'largest_contexts': [
                {
                    'id': ctx.id,
                    'name': ctx.name,
                    'user_id': ctx.user_id,
                    'total_chunks': ctx.total_chunks,
                    'total_tokens': ctx.total_tokens
                }
                for ctx in largest_contexts
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/system/health', methods=['GET'])
@jwt_required()
def get_system_health():
    """Get detailed system health information"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        health_status = monitor.get_health_status()
        current_alerts = alert_manager.check_alerts()
        
        return jsonify({
            'health': health_status,
            'current_alerts': current_alerts,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/system/metrics', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """Get detailed system metrics"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        return jsonify({
            'system': monitor.get_system_metrics(),
            'requests': monitor.get_request_metrics(),
            'application': monitor.get_application_metrics(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/cache/stats', methods=['GET'])
@jwt_required()
def get_cache_stats():
    """Get cache statistics"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        return jsonify({
            'stats': CacheMonitor.get_cache_stats(),
            'size': CacheMonitor.get_cache_size(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/cache/flush', methods=['POST'])
@jwt_required()
def flush_cache():
    """Flush all cache data"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        result = CacheMonitor.flush_cache()
        return jsonify({
            'success': result,
            'message': 'Cache flushed successfully' if result else 'Failed to flush cache'
        }), 200 if result else 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/cache/warm', methods=['POST'])
@jwt_required()
def warm_cache():
    """Warm up cache with popular data"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Warm popular contexts
        CacheWarmer.warm_popular_contexts()
        
        # Warm search cache
        CacheWarmer.warm_search_cache()
        
        return jsonify({
            'message': 'Cache warming initiated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/cleanup/orphaned', methods=['POST'])
@jwt_required()
def cleanup_orphaned_data():
    """Clean up orphaned data across the system"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    try:
        # Simple orphaned data cleanup
        cleanup_stats = {
            'orphaned_documents': 0,
            'orphaned_messages': 0,
            'orphaned_sessions': 0
        }

        # Find documents without contexts
        orphaned_docs = Document.query.filter(
            ~Document.context_id.in_(db.session.query(Context.id))
        ).all()

        for doc in orphaned_docs:
            db.session.delete(doc)
        cleanup_stats['orphaned_documents'] = len(orphaned_docs)

        # Find messages from deleted sessions
        orphaned_messages = Message.query.filter(
            ~Message.session_id.in_(db.session.query(ChatSession.id))
        ).all()

        for msg in orphaned_messages:
            db.session.delete(msg)
        cleanup_stats['orphaned_messages'] = len(orphaned_messages)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Orphaned data cleanup completed',
            'stats': cleanup_stats
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/analytics/usage', methods=['GET'])
@jwt_required()
def get_usage_analytics():
    """Get usage analytics"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Get date range from query params
        days = request.args.get('days', 7, type=int)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Daily user activity
        daily_users = db.session.query(
            func.date(ChatSession.created_at).label('date'),
            func.count(func.distinct(ChatSession.user_id)).label('active_users')
        ).filter(
            ChatSession.created_at >= start_date
        ).group_by(
            func.date(ChatSession.created_at)
        ).all()
        
        # Daily message counts
        daily_messages = db.session.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('message_count')
        ).filter(
            Message.created_at >= start_date
        ).group_by(
            func.date(Message.created_at)
        ).all()
        
        # Context creation trends
        daily_contexts = db.session.query(
            func.date(Context.created_at).label('date'),
            func.count(Context.id).label('context_count')
        ).filter(
            Context.created_at >= start_date
        ).group_by(
            func.date(Context.created_at)
        ).all()
        
        return jsonify({
            'period_days': days,
            'daily_active_users': [
                {'date': str(date), 'count': count} 
                for date, count in daily_users
            ],
            'daily_messages': [
                {'date': str(date), 'count': count} 
                for date, count in daily_messages
            ],
            'daily_contexts': [
                {'date': str(date), 'count': count} 
                for date, count in daily_contexts
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_system_logs():
    """Get system logs (placeholder - implement based on your logging setup)"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # This is a placeholder - implement based on your logging system
        # You might read from log files, database, or external logging service
        
        return jsonify({
            'message': 'Log retrieval not implemented yet',
            'suggestion': 'Implement based on your logging infrastructure'
        }), 501
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
