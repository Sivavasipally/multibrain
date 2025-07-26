"""
Performance monitoring and analytics service
"""

import time
import psutil
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from collections import defaultdict, deque
import threading
import json


class PerformanceMonitor:
    """System and application performance monitoring"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.request_times = deque(maxlen=1000)  # Keep last 1000 requests
        self.error_counts = defaultdict(int)
        self.active_requests = 0
        self.lock = threading.Lock()
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record request metrics"""
        with self.lock:
            timestamp = datetime.now(timezone.utc)
            
            self.request_times.append({
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code,
                'timestamp': timestamp.isoformat()
            })
            
            if status_code >= 400:
                self.error_counts[f"{method} {endpoint}"] += 1
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'process': {
                    'pid': os.getpid(),
                    'memory_info': psutil.Process().memory_info()._asdict(),
                    'cpu_percent': psutil.Process().cpu_percent()
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_request_metrics(self) -> Dict[str, Any]:
        """Get request performance metrics"""
        with self.lock:
            if not self.request_times:
                return {
                    'total_requests': 0,
                    'average_response_time': 0,
                    'error_rate': 0,
                    'requests_per_minute': 0
                }
            
            # Calculate metrics from recent requests
            recent_requests = list(self.request_times)
            total_requests = len(recent_requests)
            
            # Average response time
            avg_response_time = sum(req['duration'] for req in recent_requests) / total_requests
            
            # Error rate
            error_count = sum(1 for req in recent_requests if req['status_code'] >= 400)
            error_rate = (error_count / total_requests) * 100
            
            # Requests per minute (last 5 minutes)
            five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
            recent_count = sum(
                1 for req in recent_requests 
                if datetime.fromisoformat(req['timestamp'].replace('Z', '+00:00')) > five_minutes_ago
            )
            requests_per_minute = recent_count / 5
            
            # Top endpoints
            endpoint_counts = defaultdict(int)
            endpoint_times = defaultdict(list)
            
            for req in recent_requests:
                key = f"{req['method']} {req['endpoint']}"
                endpoint_counts[key] += 1
                endpoint_times[key].append(req['duration'])
            
            top_endpoints = [
                {
                    'endpoint': endpoint,
                    'count': count,
                    'avg_time': sum(endpoint_times[endpoint]) / len(endpoint_times[endpoint])
                }
                for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            return {
                'total_requests': total_requests,
                'average_response_time': round(avg_response_time, 3),
                'error_rate': round(error_rate, 2),
                'requests_per_minute': round(requests_per_minute, 2),
                'active_requests': self.active_requests,
                'top_endpoints': top_endpoints,
                'error_counts': dict(self.error_counts)
            }
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            from models import Context, Document, ChatSession, Message, db
            
            # Database metrics
            context_count = Context.query.count()
            document_count = Document.query.count()
            session_count = ChatSession.query.count()
            message_count = Message.query.count()
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            recent_contexts = Context.query.filter(Context.created_at > yesterday).count()
            recent_sessions = ChatSession.query.filter(ChatSession.created_at > yesterday).count()
            recent_messages = Message.query.filter(Message.created_at > yesterday).count()
            
            # Vector store metrics
            vector_store_dir = 'vector_store'
            vector_stores = 0
            total_vector_size = 0
            
            if os.path.exists(vector_store_dir):
                for item in os.listdir(vector_store_dir):
                    item_path = os.path.join(vector_store_dir, item)
                    if os.path.isdir(item_path):
                        vector_stores += 1
                        for root, dirs, files in os.walk(item_path):
                            total_vector_size += sum(
                                os.path.getsize(os.path.join(root, file)) 
                                for file in files
                            )
            
            return {
                'database': {
                    'contexts': context_count,
                    'documents': document_count,
                    'chat_sessions': session_count,
                    'messages': message_count
                },
                'recent_activity': {
                    'new_contexts': recent_contexts,
                    'new_sessions': recent_sessions,
                    'new_messages': recent_messages
                },
                'vector_stores': {
                    'count': vector_stores,
                    'total_size_bytes': total_vector_size,
                    'total_size_mb': round(total_vector_size / (1024 * 1024), 2)
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        system_metrics = self.get_system_metrics()
        request_metrics = self.get_request_metrics()
        
        # Determine health status
        health_issues = []
        
        if 'cpu' in system_metrics and system_metrics['cpu']['percent'] > 80:
            health_issues.append('High CPU usage')
        
        if 'memory' in system_metrics and system_metrics['memory']['percent'] > 85:
            health_issues.append('High memory usage')
        
        if 'disk' in system_metrics and system_metrics['disk']['percent'] > 90:
            health_issues.append('Low disk space')
        
        if request_metrics['error_rate'] > 10:
            health_issues.append('High error rate')
        
        if request_metrics['average_response_time'] > 5:
            health_issues.append('Slow response times')
        
        status = 'healthy' if not health_issues else 'warning' if len(health_issues) < 3 else 'critical'
        
        return {
            'status': status,
            'issues': health_issues,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_seconds': time.time() - psutil.boot_time()
        }


# Global monitor instance
monitor = PerformanceMonitor()


def track_performance(func):
    """Decorator to track function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        monitor.active_requests += 1
        
        try:
            result = func(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            monitor.active_requests -= 1
            
            # Try to get endpoint info from Flask request
            try:
                from flask import request
                endpoint = request.endpoint or request.path
                method = request.method
            except:
                endpoint = func.__name__
                method = 'UNKNOWN'
            
            monitor.record_request(endpoint, method, duration, status_code)
    
    return wrapper


class AlertManager:
    """Manage performance alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            'cpu_percent': 85,
            'memory_percent': 90,
            'disk_percent': 95,
            'error_rate': 15,
            'response_time': 10
        }
        self.alert_history = deque(maxlen=100)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        timestamp = datetime.now(timezone.utc)
        
        # Get current metrics
        system_metrics = monitor.get_system_metrics()
        request_metrics = monitor.get_request_metrics()
        
        # Check system alerts
        if 'cpu' in system_metrics:
            cpu_percent = system_metrics['cpu']['percent']
            if cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append({
                    'type': 'cpu_high',
                    'severity': 'warning',
                    'message': f'High CPU usage: {cpu_percent}%',
                    'value': cpu_percent,
                    'threshold': self.alert_thresholds['cpu_percent'],
                    'timestamp': timestamp.isoformat()
                })
        
        if 'memory' in system_metrics:
            memory_percent = system_metrics['memory']['percent']
            if memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append({
                    'type': 'memory_high',
                    'severity': 'critical',
                    'message': f'High memory usage: {memory_percent}%',
                    'value': memory_percent,
                    'threshold': self.alert_thresholds['memory_percent'],
                    'timestamp': timestamp.isoformat()
                })
        
        # Check application alerts
        error_rate = request_metrics['error_rate']
        if error_rate > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate_high',
                'severity': 'warning',
                'message': f'High error rate: {error_rate}%',
                'value': error_rate,
                'threshold': self.alert_thresholds['error_rate'],
                'timestamp': timestamp.isoformat()
            })
        
        response_time = request_metrics['average_response_time']
        if response_time > self.alert_thresholds['response_time']:
            alerts.append({
                'type': 'response_time_high',
                'severity': 'warning',
                'message': f'Slow response time: {response_time}s',
                'value': response_time,
                'threshold': self.alert_thresholds['response_time'],
                'timestamp': timestamp.isoformat()
            })
        
        # Store alerts in history
        for alert in alerts:
            self.alert_history.append(alert)
        
        return alerts
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return list(self.alert_history)[-limit:]


# Global alert manager
alert_manager = AlertManager()
