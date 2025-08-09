"""
Background Task Processing Service for RAG Chatbot PWA

This module provides a lightweight, in-memory background task processing system
that serves as an alternative to Celery for local development and simple deployments.
It supports asynchronous task execution, progress tracking, and result management.

Key Features:
- Thread-based task execution without external dependencies
- Task queuing with priority support
- Progress tracking and status monitoring
- Result storage and retrieval
- Error handling and retry mechanisms
- Task scheduling and delayed execution
- Memory-efficient task cleanup

Architecture:
- TaskQueue: In-memory priority queue for task management
- TaskWorker: Background thread for task execution
- TaskService: Main service interface for task operations
- Task: Individual task representation with metadata

Supported Task Types:
- document_processing: Process uploaded documents
- context_reprocessing: Reprocess existing contexts
- version_creation: Create context versions
- repository_cloning: Clone and process repositories
- cleanup_operations: Maintenance and cleanup tasks

Usage:
    # Submit a task
    task_id = task_service.submit_task(
        'document_processing',
        context_id=123,
        user_id=456
    )
    
    # Check task status
    status = task_service.get_task_status(task_id)
    
    # Get task result
    result = task_service.get_task_result(task_id)

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import threading
import queue
import time
import uuid
import json
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, Future

# Import logging
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('task_service')

class TaskStatus(Enum):
    """Task execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TaskResult:
    """Task execution result container"""
    success: bool
    data: Any = None
    error: str = None
    duration: float = 0.0
    completed_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'duration': self.duration,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

@dataclass
class Task:
    """Individual task representation"""
    id: str
    task_type: str
    handler: str
    args: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    max_retries: int = 3
    retry_count: int = 0
    result: Optional[TaskResult] = None
    user_id: Optional[int] = None
    context_id: Optional[int] = None
    
    def to_dict(self, include_result: bool = True) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        data = {
            'id': self.id,
            'task_type': self.task_type,
            'handler': self.handler,
            'priority': self.priority.value,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'user_id': self.user_id,
            'context_id': self.context_id
        }
        
        if include_result and self.result:
            data['result'] = self.result.to_dict()
            
        return data

class TaskQueue:
    """Thread-safe priority queue for task management"""
    
    def __init__(self):
        self.queue = queue.PriorityQueue()
        self.tasks = {}  # task_id -> Task mapping
        self.lock = threading.RLock()
        
    def submit(self, task: Task) -> str:
        """Submit a task to the queue"""
        with self.lock:
            # Store task in mapping
            self.tasks[task.id] = task
            
            # Add to priority queue (negative priority for max-heap behavior)
            priority_value = -task.priority.value
            self.queue.put((priority_value, task.created_at.timestamp(), task))
            
            logger.info(f"Submitted task {task.id}: {task.task_type} (priority: {task.priority.name})")
            return task.id
    
    def get_next_task(self, timeout: float = 1.0) -> Optional[Task]:
        """Get the next task from the queue"""
        try:
            priority, timestamp, task = self.queue.get(timeout=timeout)
            return task
        except queue.Empty:
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def update_task(self, task: Task):
        """Update a task in the queue"""
        with self.lock:
            self.tasks[task.id] = task
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from tracking"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.debug(f"Removed task {task_id} from tracking")
                return True
            return False
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        with self.lock:
            return list(self.tasks.values())
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        with self.lock:
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(hours=max_age_hours)
            
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                    and task.completed_at and task.completed_at < cutoff_time):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
            
            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

class TaskWorker:
    """Background worker thread for task execution"""
    
    def __init__(self, worker_id: int, task_queue: TaskQueue):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=1, 
                                         thread_name_prefix=f'TaskWorker-{worker_id}')
        
    def start(self):
        """Start the worker thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._work_loop, 
                                     name=f'TaskWorker-{self.worker_id}')
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started task worker {self.worker_id}")
    
    def stop(self):
        """Stop the worker thread"""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        self.executor.shutdown(wait=True)
        logger.info(f"Stopped task worker {self.worker_id}")
    
    def _work_loop(self):
        """Main worker loop"""
        logger.debug(f"Worker {self.worker_id} started processing tasks")
        
        while self.running:
            try:
                # Get next task from queue
                task = self.task_queue.get_next_task(timeout=1.0)
                if not task:
                    continue
                
                # Execute the task
                self._execute_task(task)
                
            except Exception as e:
                logger.error(f"Worker {self.worker_id} encountered error: {e}")
                log_error_with_context(e, {"worker_id": self.worker_id})
                time.sleep(0.1)  # Brief pause on error
        
        logger.debug(f"Worker {self.worker_id} stopped processing tasks")
    
    def _execute_task(self, task: Task):
        """Execute a single task"""
        logger.info(f"Worker {self.worker_id} executing task {task.id}: {task.task_type}")
        
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            self.task_queue.update_task(task)
            
            # Get task handler
            handler = task_service.get_handler(task.handler)
            if not handler:
                raise ValueError(f"No handler found for: {task.handler}")
            
            # Execute task in thread pool
            start_time = time.time()
            future = self.executor.submit(handler, task)
            result_data = future.result()  # This will block until completion
            duration = time.time() - start_time
            
            # Create successful result
            task.result = TaskResult(
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.now(timezone.utc)
            )
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            
            logger.info(f"Task {task.id} completed successfully in {duration:.2f}s")
            
        except Exception as e:
            # Handle task failure
            duration = time.time() - start_time if 'start_time' in locals() else 0
            error_message = str(e)
            
            task.result = TaskResult(
                success=False,
                error=error_message,
                duration=duration,
                completed_at=datetime.now(timezone.utc)
            )
            
            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task.started_at = None
                
                # Re-submit for retry (with delay)
                threading.Timer(2.0 ** task.retry_count, 
                               lambda: self.task_queue.submit(task)).start()
                
                logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries}): {error_message}")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.id} failed permanently after {task.retry_count} retries: {error_message}")
                log_error_with_context(e, {
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "retry_count": task.retry_count
                })
        
        finally:
            task.completed_at = datetime.now(timezone.utc)
            self.task_queue.update_task(task)

class TaskService:
    """Main task service for background processing"""
    
    def __init__(self, num_workers: int = 2):
        self.task_queue = TaskQueue()
        self.workers = []
        self.handlers = {}
        self.num_workers = num_workers
        self.running = False
        
        # Register default handlers
        self._register_default_handlers()
        
        # Start cleanup timer
        self.cleanup_timer = None
        
    def start(self):
        """Start the task service"""
        if self.running:
            return
            
        self.running = True
        
        # Start workers
        for i in range(self.num_workers):
            worker = TaskWorker(i, self.task_queue)
            worker.start()
            self.workers.append(worker)
        
        # Start cleanup timer
        self._start_cleanup_timer()
        
        logger.info(f"Task service started with {self.num_workers} workers")
    
    def stop(self):
        """Stop the task service"""
        if not self.running:
            return
            
        self.running = False
        
        # Stop cleanup timer
        if self.cleanup_timer:
            self.cleanup_timer.cancel()
        
        # Stop workers
        for worker in self.workers:
            worker.stop()
        self.workers.clear()
        
        logger.info("Task service stopped")
    
    def submit_task(self, task_type: str, handler: str = None, 
                   priority: TaskPriority = TaskPriority.NORMAL, 
                   user_id: int = None, context_id: int = None,
                   max_retries: int = 3, **kwargs) -> str:
        """Submit a new task for processing"""
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Determine handler
        if not handler:
            handler = task_type
        
        # Create task
        task = Task(
            id=task_id,
            task_type=task_type,
            handler=handler,
            args=kwargs,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            max_retries=max_retries,
            user_id=user_id,
            context_id=context_id
        )
        
        # Submit to queue
        self.task_queue.submit(task)
        
        logger.info(f"Submitted {task_type} task {task_id} for user {user_id}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get task status by ID"""
        task = self.task_queue.get_task(task_id)
        return task.status.value if task else None
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get complete task information"""
        task = self.task_queue.get_task(task_id)
        return task.to_dict() if task else None
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result by ID"""
        task = self.task_queue.get_task(task_id)
        if task and task.result:
            return task.result.to_dict()
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.task_queue.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now(timezone.utc)
            self.task_queue.update_task(task)
            logger.info(f"Cancelled task {task_id}")
            return True
        return False
    
    def get_user_tasks(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tasks for a specific user"""
        all_tasks = self.task_queue.get_all_tasks()
        user_tasks = [task for task in all_tasks if task.user_id == user_id]
        
        # Sort by creation time (newest first)
        user_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return [task.to_dict() for task in user_tasks[:limit]]
    
    def get_context_tasks(self, context_id: int) -> List[Dict[str, Any]]:
        """Get tasks for a specific context"""
        all_tasks = self.task_queue.get_all_tasks()
        context_tasks = [task for task in all_tasks if task.context_id == context_id]
        
        # Sort by creation time (newest first)
        context_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return [task.to_dict() for task in context_tasks]
    
    def register_handler(self, name: str, handler: Callable):
        """Register a task handler"""
        self.handlers[name] = handler
        logger.debug(f"Registered task handler: {name}")
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """Get a task handler by name"""
        return self.handlers.get(name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task service statistics"""
        all_tasks = self.task_queue.get_all_tasks()
        
        stats = {
            'total_tasks': len(all_tasks),
            'workers': len(self.workers),
            'running': self.running
        }
        
        # Count by status
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for task in all_tasks if task.status == status)
        stats['status_counts'] = status_counts
        
        # Count by type
        type_counts = {}
        for task in all_tasks:
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
        stats['type_counts'] = type_counts
        
        return stats
    
    def _register_default_handlers(self):
        """Register default task handlers"""
        # Import handlers to avoid circular imports
        from services.task_handlers import (
            document_processing_handler,
            context_reprocessing_handler,
            version_creation_handler,
            repository_cloning_handler,
            cleanup_operations_handler
        )
        
        self.register_handler('document_processing', document_processing_handler)
        self.register_handler('context_reprocessing', context_reprocessing_handler)
        self.register_handler('version_creation', version_creation_handler)
        self.register_handler('repository_cloning', repository_cloning_handler)
        self.register_handler('cleanup_operations', cleanup_operations_handler)
    
    def _start_cleanup_timer(self):
        """Start periodic cleanup timer"""
        def cleanup():
            if self.running:
                try:
                    self.task_queue.cleanup_old_tasks()
                except Exception as e:
                    logger.error(f"Error during task cleanup: {e}")
                
                # Schedule next cleanup
                self.cleanup_timer = threading.Timer(3600.0, cleanup)  # Every hour
                self.cleanup_timer.daemon = True
                self.cleanup_timer.start()
        
        cleanup()

# Global task service instance
task_service = TaskService()

def start_task_service(num_workers: int = 2):
    """Start the global task service"""
    global task_service
    if not task_service.running:
        task_service.num_workers = num_workers
        task_service.start()

def stop_task_service():
    """Stop the global task service"""
    global task_service
    if task_service.running:
        task_service.stop()