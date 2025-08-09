"""
Logging configuration for RAG Chatbot PWA
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color to log messages for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Color the level name
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    console_output: bool = True,
    json_format: bool = False
):
    """
    Setup logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, uses logs/ragchatbot.log)
        max_file_size_mb: Maximum size of log file in MB before rotation
        backup_count: Number of backup log files to keep
        console_output: Whether to output logs to console
        json_format: Whether to use JSON format for file logging
    """
    
    # Convert log level string to logging constant
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Default log file path
    if log_file is None:
        log_file = os.path.join(log_dir, 'ragchatbot.log')
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Use colored formatter for console
        console_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        
        root_logger.addHandler(console_handler)
    
    # File formatter
    if json_format:
        # JSON formatter for structured logging
        file_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
        file_formatter = logging.Formatter(file_format)
    else:
        # Standard text formatter
        file_format = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)s.%(funcName)s:%(lineno)d | %(message)s'
        file_formatter = logging.Formatter(
            file_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels for third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('git').setLevel(logging.WARNING)
    
    # Create application-specific loggers
    app_logger = logging.getLogger('ragchatbot')
    app_logger.setLevel(log_level)
    
    vector_logger = logging.getLogger('ragchatbot.vector')
    vector_logger.setLevel(log_level)
    
    llm_logger = logging.getLogger('ragchatbot.llm')
    llm_logger.setLevel(log_level)
    
    repo_logger = logging.getLogger('ragchatbot.repository')
    repo_logger.setLevel(log_level)
    
    # Log the logging setup completion
    app_logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}, File: {log_file}")
    
    return {
        'app': app_logger,
        'vector': vector_logger,
        'llm': llm_logger,
        'repository': repo_logger
    }


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name under the ragchatbot namespace"""
    return logging.getLogger(f'ragchatbot.{name}')


def log_request_info(request, response=None, duration=None):
    """Log HTTP request information"""
    logger = get_logger('requests')
    
    # Basic request info
    log_data = {
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    
    # Add response info if available
    if response:
        log_data['status_code'] = response.status_code
    
    # Add duration if available
    if duration:
        log_data['duration_ms'] = f"{duration * 1000:.2f}"
    
    # Log the request
    message_parts = [f"{log_data['method']} {log_data['path']}"]
    
    if 'status_code' in log_data:
        message_parts.append(f"[{log_data['status_code']}]")
    
    if 'duration_ms' in log_data:
        message_parts.append(f"({log_data['duration_ms']}ms)")
    
    message_parts.append(f"from {log_data['remote_addr']}")
    
    logger.info(" ".join(message_parts))


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None):
    """Log an error with additional context information"""
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error)
    }
    
    if context:
        error_info.update(context)
    
    # Create a detailed error message
    message_parts = [f"{error_info['error_type']}: {error_info['error_message']}"]
    
    if context:
        context_parts = []
        for key, value in context.items():
            if key not in ['error_type', 'error_message']:
                context_parts.append(f"{key}={value}")
        
        if context_parts:
            message_parts.append(f"Context: {', '.join(context_parts)}")
    
    logger.error(" | ".join(message_parts), exc_info=True)


class RequestLoggingMiddleware:
    """Middleware to log HTTP requests and responses"""
    
    def __init__(self, app, logger_name='requests'):
        self.app = app
        self.logger = get_logger(logger_name)
    
    def __call__(self, environ, start_response):
        """WSGI middleware to log requests"""
        import time
        from werkzeug.wrappers import Request, Response
        
        request = Request(environ)
        start_time = time.time()
        
        def logging_start_response(status, response_headers, exc_info=None):
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract status code
            status_code = int(status.split(' ', 1)[0])
            
            # Log the request
            self.logger.info(
                f"{request.method} {request.path} [{status_code}] "
                f"({duration*1000:.2f}ms) from {request.remote_addr}"
            )
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, logging_start_response)


# Example usage and configuration
if __name__ == "__main__":
    # Setup logging with different configurations
    
    # Development configuration
    loggers = setup_logging(
        log_level="DEBUG",
        console_output=True,
        json_format=False
    )
    
    # Test the loggers
    app_logger = loggers['app']
    app_logger.debug("This is a debug message")
    app_logger.info("This is an info message")
    app_logger.warning("This is a warning message")
    app_logger.error("This is an error message")
    app_logger.critical("This is a critical message")
    
    # Test error logging with context
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        log_error_with_context(
            app_logger, 
            e, 
            {'user_id': 123, 'operation': 'test_logging'}
        )