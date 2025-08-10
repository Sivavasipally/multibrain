"""
Logging Dashboard Service - Real-time Monitoring and Analytics

This service provides comprehensive monitoring and analytics capabilities for
the RAG chatbot system, including real-time metrics, performance tracking,
and detailed operation insights.

Features:
- Real-time performance metrics
- Operation statistics and trends
- User activity monitoring
- System health indicators
- Error tracking and analysis
- Resource usage monitoring
- Custom analytics queries

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading

from logging_config import get_logger

logger = get_logger('logging_dashboard')

@dataclass
class MetricSummary:
    """Summary metrics for a time period"""
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time: float
    total_tokens_used: int
    total_chunks_processed: int
    unique_users: int
    peak_concurrent_operations: int

@dataclass
class SystemHealth:
    """System health indicators"""
    status: str  # healthy, warning, critical
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_contexts: int
    active_sessions: int
    error_rate: float
    response_time_p95: float

class LoggingDashboard:
    """Real-time logging dashboard and analytics service"""
    
    def __init__(self, max_history_hours: int = 24):
        self.max_history_hours = max_history_hours
        self.metrics_history = deque(maxlen=max_history_hours * 60)  # Store per-minute metrics
        self.operations_log = deque(maxlen=10000)  # Last 10k operations
        self.user_sessions = defaultdict(list)
        self.error_log = deque(maxlen=1000)  # Last 1k errors
        self.performance_metrics = defaultdict(list)
        self.real_time_stats = {
            'active_operations': 0,
            'total_requests_today': 0,
            'average_response_time': 0.0,
            'current_error_rate': 0.0,
            'active_users': set(),
            'peak_concurrent_operations': 0
        }
        self.lock = threading.RLock()
        
        # Start background metrics collection
        self._start_metrics_collection()
    
    def _start_metrics_collection(self):
        """Start background thread for metrics collection"""
        def collect_metrics():
            while True:
                try:
                    self._collect_minute_metrics()
                    time.sleep(60)  # Collect every minute
                except Exception as e:
                    logger.error(f"Error in metrics collection: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        logger.info("Started background metrics collection")
    
    def _collect_minute_metrics(self):
        """Collect and store per-minute metrics"""
        with self.lock:
            current_time = datetime.now(timezone.utc)
            
            # Calculate metrics for the last minute
            recent_ops = [op for op in self.operations_log 
                         if current_time - op['timestamp'] <= timedelta(minutes=1)]
            
            if recent_ops:
                successful_ops = [op for op in recent_ops if op['success']]
                failed_ops = [op for op in recent_ops if not op['success']]
                
                avg_response_time = sum(op['response_time'] for op in recent_ops) / len(recent_ops)
                total_tokens = sum(op.get('tokens_used', 0) for op in recent_ops)
                total_chunks = sum(op.get('chunks_processed', 0) for op in recent_ops)
                unique_users = len(set(op.get('user_id') for op in recent_ops if op.get('user_id')))
                
                minute_metrics = {
                    'timestamp': current_time.isoformat(),
                    'total_operations': len(recent_ops),
                    'successful_operations': len(successful_ops),
                    'failed_operations': len(failed_ops),
                    'average_response_time': avg_response_time,
                    'total_tokens_used': total_tokens,
                    'total_chunks_processed': total_chunks,
                    'unique_users': unique_users
                }
                
                self.metrics_history.append(minute_metrics)
    
    def log_operation(self, operation_type: str, operation_data: Dict[str, Any]):
        """Log an operation for dashboard tracking"""
        with self.lock:
            operation_entry = {
                'timestamp': datetime.now(timezone.utc),
                'operation_type': operation_type,
                'success': operation_data.get('success', True),
                'response_time': operation_data.get('response_time', 0.0),
                'user_id': operation_data.get('user_id'),
                'session_id': operation_data.get('session_id'),
                'tokens_used': operation_data.get('tokens_used', 0),
                'chunks_processed': operation_data.get('chunks_processed', 0),
                'context_ids': operation_data.get('context_ids', []),
                'error_details': operation_data.get('error_details')
            }
            
            self.operations_log.append(operation_entry)
            
            # Update real-time stats
            if operation_data.get('user_id'):
                self.real_time_stats['active_users'].add(operation_data['user_id'])
            
            if not operation_data.get('success', True):
                self._log_error(operation_entry)
    
    def _log_error(self, operation_entry: Dict[str, Any]):
        """Log an error for tracking"""
        error_entry = {
            'timestamp': operation_entry['timestamp'],
            'operation_type': operation_entry['operation_type'],
            'user_id': operation_entry.get('user_id'),
            'error_details': operation_entry.get('error_details', 'Unknown error'),
            'context': {
                'session_id': operation_entry.get('session_id'),
                'context_ids': operation_entry.get('context_ids', [])
            }
        }
        
        self.error_log.append(error_entry)
    
    def get_dashboard_data(self, time_range: str = '1h') -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        with self.lock:
            current_time = datetime.now(timezone.utc)
            
            # Parse time range
            if time_range == '1h':
                since = current_time - timedelta(hours=1)
            elif time_range == '24h':
                since = current_time - timedelta(hours=24)
            elif time_range == '7d':
                since = current_time - timedelta(days=7)
            else:
                since = current_time - timedelta(hours=1)
            
            # Filter operations by time range
            recent_operations = [op for op in self.operations_log 
                               if op['timestamp'] >= since]
            
            # Calculate summary metrics
            total_ops = len(recent_operations)
            successful_ops = len([op for op in recent_operations if op['success']])
            failed_ops = total_ops - successful_ops
            
            avg_response_time = (sum(op['response_time'] for op in recent_operations) / total_ops) if total_ops > 0 else 0
            total_tokens = sum(op.get('tokens_used', 0) for op in recent_operations)
            total_chunks = sum(op.get('chunks_processed', 0) for op in recent_operations)
            unique_users = len(set(op.get('user_id') for op in recent_operations if op.get('user_id')))
            
            # Get operation type breakdown
            operation_types = defaultdict(int)
            for op in recent_operations:
                operation_types[op['operation_type']] += 1
            
            # Get recent errors
            recent_errors = [error for error in self.error_log 
                           if error['timestamp'] >= since]
            
            # Get performance trends (last hour in 5-minute buckets)
            performance_buckets = self._get_performance_trends(since)
            
            dashboard_data = {
                'summary': {
                    'time_range': time_range,
                    'total_operations': total_ops,
                    'successful_operations': successful_ops,
                    'failed_operations': failed_ops,
                    'success_rate': (successful_ops / total_ops * 100) if total_ops > 0 else 100,
                    'average_response_time': avg_response_time,
                    'total_tokens_used': total_tokens,
                    'total_chunks_processed': total_chunks,
                    'unique_users': unique_users,
                    'active_users_now': len(self.real_time_stats['active_users'])
                },
                'operation_breakdown': dict(operation_types),
                'performance_trends': performance_buckets,
                'recent_errors': [
                    {
                        'timestamp': error['timestamp'].isoformat(),
                        'operation_type': error['operation_type'],
                        'error_details': error['error_details'][:200] + ('...' if len(error['error_details']) > 200 else ''),
                        'user_id': error.get('user_id')
                    }
                    for error in recent_errors[-10:]  # Last 10 errors
                ],
                'system_health': self._get_system_health(),
                'top_users': self._get_top_users(recent_operations),
                'context_usage': self._get_context_usage(recent_operations)
            }
            
            return dashboard_data
    
    def _get_performance_trends(self, since: datetime) -> List[Dict[str, Any]]:
        """Get performance trends in time buckets"""
        trends = []
        bucket_size = timedelta(minutes=5)
        current = since
        
        while current < datetime.now(timezone.utc):
            bucket_end = current + bucket_size
            bucket_ops = [op for op in self.operations_log 
                         if current <= op['timestamp'] < bucket_end]
            
            if bucket_ops:
                avg_response_time = sum(op['response_time'] for op in bucket_ops) / len(bucket_ops)
                success_rate = len([op for op in bucket_ops if op['success']]) / len(bucket_ops) * 100
            else:
                avg_response_time = 0
                success_rate = 100
            
            trends.append({
                'timestamp': current.isoformat(),
                'operations_count': len(bucket_ops),
                'average_response_time': avg_response_time,
                'success_rate': success_rate
            })
            
            current = bucket_end
        
        return trends
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        current_time = datetime.now(timezone.utc)
        last_hour = current_time - timedelta(hours=1)
        
        recent_ops = [op for op in self.operations_log if op['timestamp'] >= last_hour]
        
        if recent_ops:
            error_rate = len([op for op in recent_ops if not op['success']]) / len(recent_ops) * 100
            avg_response_time = sum(op['response_time'] for op in recent_ops) / len(recent_ops)
            
            # Determine health status
            if error_rate > 10 or avg_response_time > 5:
                status = 'critical'
            elif error_rate > 5 or avg_response_time > 3:
                status = 'warning'
            else:
                status = 'healthy'
        else:
            status = 'healthy'
            error_rate = 0
            avg_response_time = 0
        
        return {
            'status': status,
            'error_rate': error_rate,
            'average_response_time': avg_response_time,
            'active_operations': self.real_time_stats['active_operations'],
            'last_updated': current_time.isoformat()
        }
    
    def _get_top_users(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top users by activity"""
        user_stats = defaultdict(lambda: {'operations': 0, 'tokens': 0, 'avg_response_time': 0, 'total_time': 0})
        
        for op in operations:
            user_id = op.get('user_id')
            if user_id:
                user_stats[user_id]['operations'] += 1
                user_stats[user_id]['tokens'] += op.get('tokens_used', 0)
                user_stats[user_id]['total_time'] += op.get('response_time', 0)
        
        # Calculate averages and sort
        top_users = []
        for user_id, stats in user_stats.items():
            if stats['operations'] > 0:
                stats['avg_response_time'] = stats['total_time'] / stats['operations']
            
            top_users.append({
                'user_id': user_id,
                'operations': stats['operations'],
                'tokens_used': stats['tokens'],
                'avg_response_time': stats['avg_response_time']
            })
        
        return sorted(top_users, key=lambda x: x['operations'], reverse=True)[:10]
    
    def _get_context_usage(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get context usage statistics"""
        context_usage = defaultdict(int)
        
        for op in operations:
            context_ids = op.get('context_ids', [])
            for context_id in context_ids:
                context_usage[str(context_id)] += 1
        
        return dict(context_usage)
    
    def get_operation_details(self, operation_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get detailed operation logs"""
        with self.lock:
            operations = list(self.operations_log)[-limit:]
            
            return [
                {
                    'timestamp': op['timestamp'].isoformat(),
                    'operation_type': op['operation_type'],
                    'success': op['success'],
                    'response_time': op['response_time'],
                    'user_id': op.get('user_id'),
                    'session_id': op.get('session_id'),
                    'tokens_used': op.get('tokens_used', 0),
                    'chunks_processed': op.get('chunks_processed', 0),
                    'context_ids': op.get('context_ids', []),
                    'error_details': op.get('error_details') if not op['success'] else None
                }
                for op in reversed(operations)
            ]
    
    def get_metrics_export(self, format_type: str = 'json') -> str:
        """Export metrics in various formats"""
        with self.lock:
            if format_type == 'json':
                export_data = {
                    'export_timestamp': datetime.now(timezone.utc).isoformat(),
                    'metrics_history': list(self.metrics_history),
                    'operations_summary': {
                        'total_operations': len(self.operations_log),
                        'operation_types': dict(defaultdict(int)),
                        'error_count': len(self.error_log)
                    },
                    'system_stats': self.real_time_stats.copy()
                }
                
                # Convert set to list for JSON serialization
                export_data['system_stats']['active_users'] = len(export_data['system_stats']['active_users'])
                
                return json.dumps(export_data, indent=2)
            
            else:
                return "Unsupported export format"

# Global dashboard instance
logging_dashboard = LoggingDashboard()

# Integration function for the detailed logger
def log_to_dashboard(operation_type: str, operation_data: Dict[str, Any]):
    """Integration function for logging to dashboard"""
    try:
        logging_dashboard.log_operation(operation_type, operation_data)
    except Exception as e:
        logger.error(f"Failed to log to dashboard: {e}")

# Export convenience functions
def get_dashboard_data(time_range: str = '1h') -> Dict[str, Any]:
    """Get dashboard data for specified time range"""
    return logging_dashboard.get_dashboard_data(time_range)

def get_operation_details(limit: int = 100) -> List[Dict[str, Any]]:
    """Get detailed operation logs"""
    return logging_dashboard.get_operation_details(limit=limit)