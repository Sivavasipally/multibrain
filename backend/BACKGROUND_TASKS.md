# Background Task Processing System Documentation

## Overview

The Background Task Processing System provides asynchronous execution capabilities for long-running operations in the RAG Chatbot PWA. This lightweight, in-memory system serves as a Celery alternative for local development and simple deployments, offering task queuing, progress tracking, and result management without external dependencies.

## Key Features

### 🔄 **Asynchronous Execution**
- Thread-based task execution without blocking API requests
- Priority-based task queuing (low, normal, high, urgent)
- Configurable number of worker threads
- Automatic retry mechanisms with exponential backoff

### 📊 **Progress Monitoring**
- Real-time task status tracking (pending, running, completed, failed)
- Progress percentage updates during execution
- Task duration measurement and estimation
- Comprehensive task result storage

### 🔧 **Task Management**
- Task cancellation for pending tasks
- User-specific task filtering and history
- Context-specific task tracking
- Automatic cleanup of old completed tasks

### 🛡️ **Error Handling**
- Configurable retry attempts with intelligent backoff
- Comprehensive error logging and context preservation
- Graceful degradation on task failures
- Task result preservation for debugging

## Architecture

### Core Components

#### TaskService
The main service interface providing task management:

```python
class TaskService:
    def submit_task(task_type, priority=TaskPriority.NORMAL, **kwargs) -> str
    def get_task_status(task_id) -> str
    def get_task_result(task_id) -> Dict[str, Any]
    def cancel_task(task_id) -> bool
    def get_stats() -> Dict[str, Any]
```

#### Task Queue
Thread-safe priority queue for task management:

```python
class TaskQueue:
    def submit(task: Task) -> str
    def get_next_task(timeout: float) -> Optional[Task]
    def cleanup_old_tasks(max_age_hours: int)
```

#### Task Workers
Background threads executing tasks:

```python
class TaskWorker:
    def start()  # Start worker thread
    def stop()   # Stop worker gracefully
    def _execute_task(task: Task)  # Execute individual task
```

### Task Types

#### document_processing
Process uploaded documents for RAG operations:
- **Purpose**: Extract text, create chunks, build vector indexes
- **Duration**: 2-10 minutes (depends on document count/size)
- **Parameters**: `context_id`, `force_reprocess`
- **Results**: Processing statistics, chunk counts, vector store path

#### context_reprocessing  
Reprocess all documents in a context:
- **Purpose**: Apply new chunking strategies or update embeddings
- **Duration**: 5-15 minutes
- **Parameters**: `context_id`, `new_chunk_strategy`, `clear_existing`
- **Results**: Reprocessing statistics

#### version_creation
Create context versions:
- **Purpose**: Schedule version creation or batch operations
- **Duration**: 30 seconds - 2 minutes
- **Parameters**: `context_id`, `description`, `version_type`, `force_major`
- **Results**: Version information

#### repository_cloning
Clone and process repositories:
- **Purpose**: Clone GitHub/Bitbucket repositories and process files
- **Duration**: 3-20 minutes (depends on repository size)
- **Parameters**: `context_id`, `repo_url`, `branch`, `access_token`
- **Results**: Clone statistics and processing results

#### cleanup_operations
System maintenance tasks:
- **Purpose**: Clean up old files, optimize databases, clear caches
- **Duration**: 1-5 minutes
- **Parameters**: `operation_type`, `max_age_days`, `dry_run`
- **Results**: Cleanup statistics and space freed

## API Endpoints

### Task Management

#### `POST /api/tasks`
Submit a new background task.

**Request Body:**
```json
{
  "task_type": "document_processing",
  "priority": "high",
  "context_id": 123,
  "parameters": {
    "force_reprocess": false
  }
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "message": "Task submitted successfully",
  "task_type": "document_processing",
  "status": "pending",
  "estimated_duration": "5-10 minutes"
}
```

#### `GET /api/tasks`
Get user's tasks with filtering.

**Query Parameters:**
- `status`: Filter by status (pending, running, completed, failed)
- `task_type`: Filter by task type
- `limit`: Maximum tasks to return (default: 20)
- `offset`: Number of tasks to skip

#### `GET /api/tasks/{task_id}`
Get specific task details.

**Response:**
```json
{
  "task": {
    "id": "uuid-string",
    "task_type": "document_processing",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:00Z",
    "result": {
      "success": true,
      "data": {
        "processed_count": 5,
        "total_chunks": 150,
        "total_tokens": 12000
      },
      "duration": 280.5
    }
  }
}
```

#### `DELETE /api/tasks/{task_id}`
Cancel a pending task.

#### `GET /api/tasks/stats`
Get task system statistics.

#### `GET /api/contexts/{id}/tasks`
Get tasks for a specific context.

### Async Processing

#### `POST /api/upload/{context_id}/process-async`
Submit document processing as background task.

**Request Body:**
```json
{
  "force_reprocess": false,
  "priority": "high"
}
```

**Response (202 Accepted):**
```json
{
  "message": "Document processing task submitted successfully",
  "task_id": "uuid-string",
  "context_id": 123,
  "documents_to_process": 5,
  "estimated_duration": "5-10 minutes",
  "monitor_url": "/api/tasks/uuid-string"
}
```

## Usage Examples

### Processing Documents Asynchronously

```bash
# Upload documents first
curl -X POST "/api/upload/123" \
     -H "Authorization: Bearer <token>" \
     -F "files=@document1.pdf" \
     -F "files=@document2.txt"

# Submit for async processing
curl -X POST "/api/upload/123/process-async" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"priority": "high"}'

# Monitor task progress
curl -X GET "/api/tasks/{task_id}" \
     -H "Authorization: Bearer <token>"
```

### Repository Processing

```bash
# Submit repository cloning task
curl -X POST "/api/tasks" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "task_type": "repository_cloning",
       "priority": "normal",
       "context_id": 123,
       "parameters": {
         "repo_url": "https://github.com/user/repo",
         "branch": "main",
         "access_token": "optional-token"
       }
     }'
```

### System Cleanup

```bash
# Submit cleanup task (admin only)
curl -X POST "/api/tasks" \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "task_type": "cleanup_operations",
       "priority": "low",
       "parameters": {
         "operation_type": "general",
         "max_age_days": 30,
         "dry_run": false
       }
     }'
```

## Integration Guide

### Starting the Task Service

The task service is automatically started when the Flask application runs:

```python
# In app_local.py and app.py
from services.task_service import start_task_service

if __name__ == '__main__':
    # Start background task service
    start_task_service(num_workers=2)  # Local: 2 workers
    # start_task_service(num_workers=3)  # Production: 3 workers
    
    app.run(...)
```

### Custom Task Handlers

Add custom task handlers by registering them with the service:

```python
from services.task_service import task_service

def my_custom_handler(task):
    """Custom task handler"""
    # Access parameters via task.args
    param1 = task.args.get('param1')
    
    # Update progress
    task.progress = 50
    
    # Do work...
    result = perform_operation(param1)
    
    return result

# Register handler
task_service.register_handler('my_custom_task', my_custom_handler)

# Submit task
task_id = task_service.submit_task('my_custom_task', param1='value')
```

### Error Handling in Handlers

```python
def error_prone_handler(task):
    try:
        # Risky operation
        result = risky_operation(task.args)
        return result
        
    except SpecificError as e:
        # Handle specific errors
        logger.error(f"Specific error in task {task.id}: {e}")
        raise  # Re-raise to trigger retry
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in task {task.id}: {e}")
        # Could choose to not re-raise to avoid retries
        return {'error': str(e), 'success': False}
```

## Configuration

### Environment Variables

```bash
# Task service configuration (optional)
TASK_WORKERS=2              # Number of worker threads
TASK_CLEANUP_INTERVAL=3600  # Cleanup interval in seconds
TASK_MAX_RETRIES=3          # Default max retries
TASK_RETRY_DELAY=2          # Base retry delay in seconds

# Task-specific settings
MAX_PROCESSING_TIME=1800    # Maximum task execution time (30 min)
BACKGROUND_PROCESSING=true  # Enable background processing
```

### Service Configuration

```python
# In services/task_service.py
class TaskService:
    def __init__(self, num_workers: int = 2):
        self.num_workers = num_workers
        # ... other configuration
```

## Monitoring and Debugging

### Task Status Monitoring

```python
# Get system statistics
stats = task_service.get_stats()
print(f"Total tasks: {stats['total_tasks']}")
print(f"Running workers: {stats['workers']}")
print(f"Status counts: {stats['status_counts']}")
```

### Logging

Enable debug logging for task operations:

```python
import logging
logging.getLogger('task_service').setLevel(logging.DEBUG)
logging.getLogger('task_handlers').setLevel(logging.DEBUG)
```

### Performance Monitoring

Monitor task performance and resource usage:

```bash
# Check task processing times
grep "Task.*completed" logs/app.log | tail -20

# Monitor memory usage
ps aux | grep python | grep app_local.py

# Check worker thread status  
pstree -p $(pgrep -f app_local.py)
```

## Best Practices

### 1. Task Design
- Keep tasks idempotent (safe to retry)
- Use appropriate priority levels
- Include progress updates for long-running tasks
- Implement proper error handling and logging

### 2. Resource Management
- Monitor memory usage for large document processing
- Use appropriate worker thread counts
- Implement task timeouts for runaway operations
- Clean up temporary files and resources

### 3. User Experience
- Provide clear progress feedback
- Offer task cancellation for pending tasks
- Use appropriate estimated durations
- Handle task failures gracefully

### 4. Security
- Validate user permissions for all tasks
- Sanitize task parameters and inputs
- Limit task submission rates per user
- Audit and log all task operations

## Troubleshooting

### Common Issues

#### 1. Tasks Not Starting
```python
# Check if task service is running
if task_service.running:
    print("Task service is running")
    print(f"Workers: {len(task_service.workers)}")
else:
    print("Task service is not started")
    start_task_service()
```

#### 2. High Memory Usage
```python
# Monitor task queue size
stats = task_service.get_stats()
if stats['status_counts']['pending'] > 100:
    print("High task queue - consider more workers")

# Clean up old tasks manually
task_service.task_queue.cleanup_old_tasks(max_age_hours=12)
```

#### 3. Task Handler Errors
```python
# Check task results for errors
task_dict = task_service.get_task(task_id)
if task_dict['status'] == 'failed':
    print(f"Task failed: {task_dict['result']['error']}")
    print(f"Retry count: {task_dict['retry_count']}")
```

### Debug Mode

Enable comprehensive debugging:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor individual task execution
task_id = task_service.submit_task('test_task', debug=True)
while True:
    status = task_service.get_task_status(task_id)
    if status in ['completed', 'failed']:
        break
    time.sleep(1)
```

## Performance Characteristics

### Scalability Limits
- **Concurrent Tasks**: Limited by worker thread count (2-5 recommended)
- **Memory Usage**: ~50-100MB per worker for document processing
- **Task Queue**: In-memory storage (thousands of tasks supported)
- **Throughput**: 10-50 tasks/hour depending on task complexity

### Optimization Tips
1. **Worker Tuning**: Start with 2 workers, increase based on CPU cores
2. **Memory Management**: Monitor memory usage during large document processing
3. **Task Batching**: Group related operations into single tasks when possible
4. **Resource Cleanup**: Implement proper cleanup in task handlers

## Future Enhancements

### Planned Features
1. **Persistent Storage**: Database-backed task queue for durability
2. **Distributed Processing**: Multi-node task execution
3. **Advanced Scheduling**: Cron-like task scheduling
4. **Task Dependencies**: Chain tasks with dependencies
5. **Real-time Updates**: WebSocket-based progress notifications

### Migration Path
The current in-memory system can be upgraded to Celery/Redis without changing the API:

```python
# Future Celery integration
from celery import Celery

class CeleryTaskService(TaskService):
    def __init__(self):
        self.celery = Celery('rag_chatbot')
        # Maintain same API interface
```

## Conclusion

The Background Task Processing System provides robust asynchronous execution capabilities for the RAG Chatbot PWA without external dependencies. It enables responsive user experiences by handling long-running operations in the background while providing comprehensive monitoring and management tools.