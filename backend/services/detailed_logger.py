"""
Advanced Logging System for RAG Chatbot - Detailed Operation Tracking

This module provides comprehensive logging capabilities for tracking detailed operations
across the RAG pipeline including chunking, vector operations, LLM interactions,
and performance metrics.

Features:
- Detailed chunk processing logs with metadata
- RAG pipeline performance tracking
- LLM interaction monitoring with token usage
- Vector search operation logging
- Context creation and document processing logs
- Performance metrics and timing analysis
- Error tracking with full context
- User activity and session tracking

Author: RAG Chatbot Development Team
Version: 2.0.0
"""

import time
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from contextlib import contextmanager

from logging_config import get_logger

# Initialize loggers for different components
chunk_logger = get_logger('chunk_operations')
rag_logger = get_logger('rag_pipeline')
llm_logger = get_logger('llm_interactions')
vector_logger = get_logger('vector_operations')
context_logger = get_logger('context_management')
performance_logger = get_logger('performance_metrics')
user_activity_logger = get_logger('user_activity')

@dataclass
class ChunkMetadata:
    """Metadata for chunk processing operations"""
    chunk_id: str
    source_file: str
    file_type: str
    chunk_index: int
    chunk_size: int
    chunk_strategy: str
    processing_time: float
    extraction_method: str
    language_detected: Optional[str] = None
    token_count: Optional[int] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    similarity_score: Optional[float] = None

@dataclass
class RAGOperationMetrics:
    """Comprehensive metrics for RAG operations"""
    operation_id: str
    user_id: Optional[int]
    session_id: Optional[int]
    query: str
    contexts_searched: List[int]
    total_chunks_retrieved: int
    chunks_by_context: Dict[str, int]
    retrieval_time: float
    llm_generation_time: float
    total_response_time: float
    tokens_input: int
    tokens_output: int
    model_used: str
    response_length: int
    success: bool
    error_details: Optional[str] = None

@dataclass
class VectorOperationLog:
    """Vector store operation logging"""
    operation_id: str
    operation_type: str  # create, search, update, delete
    vector_store_path: str
    context_id: int
    embedding_model: str
    operation_time: float
    chunks_processed: Optional[int] = None
    search_query: Optional[str] = None
    top_k: Optional[int] = None
    results_count: Optional[int] = None
    average_similarity: Optional[float] = None
    success: bool = True
    error_details: Optional[str] = None

@dataclass
class ContextCreationLog:
    """Context creation and management logging"""
    context_id: int
    user_id: int
    context_name: str
    context_type: str  # repository, documents, links, mixed
    sources: List[Dict[str, Any]]
    total_files: int
    total_size_bytes: int
    processing_time: float
    chunks_created: int
    embedding_model: str
    success: bool
    error_details: Optional[str] = None

class DetailedLogger:
    """Enhanced logging system for comprehensive operation tracking"""
    
    def __init__(self):
        self.operation_stack = threading.local()
        self.session_metrics = {}
        
    def generate_operation_id(self) -> str:
        """Generate unique operation ID"""
        return f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    @contextmanager
    def track_operation(self, operation_name: str, **kwargs):
        """Context manager for tracking operation performance"""
        operation_id = self.generate_operation_id()
        start_time = time.time()
        
        # Initialize operation tracking
        if not hasattr(self.operation_stack, 'operations'):
            self.operation_stack.operations = []
        
        operation_data = {
            'operation_id': operation_id,
            'operation_name': operation_name,
            'start_time': start_time,
            'metadata': kwargs
        }
        
        self.operation_stack.operations.append(operation_data)
        
        try:
            performance_logger.info(
                f"🚀 Starting operation: {operation_name} | ID: {operation_id}",
                extra={
                    'operation_id': operation_id,
                    'operation_name': operation_name,
                    'metadata': kwargs
                }
            )
            yield operation_id
            
        except Exception as e:
            operation_data['error'] = str(e)
            operation_data['success'] = False
            performance_logger.error(
                f"❌ Operation failed: {operation_name} | ID: {operation_id} | Error: {str(e)}",
                extra={
                    'operation_id': operation_id,
                    'operation_name': operation_name,
                    'error': str(e),
                    'duration': time.time() - start_time
                }
            )
            raise
            
        finally:
            duration = time.time() - start_time
            operation_data['duration'] = duration
            operation_data['success'] = operation_data.get('success', True)
            
            performance_logger.info(
                f"✅ Operation completed: {operation_name} | ID: {operation_id} | Duration: {duration:.3f}s",
                extra={
                    'operation_id': operation_id,
                    'operation_name': operation_name,
                    'duration': duration,
                    'success': operation_data['success']
                }
            )
            
            self.operation_stack.operations.pop()
    
    def log_chunk_processing(self, chunk_metadata: ChunkMetadata):
        """Log detailed chunk processing information"""
        chunk_logger.info(
            f"📄 Chunk processed: {chunk_metadata.source_file} | "
            f"Index: {chunk_metadata.chunk_index} | "
            f"Size: {chunk_metadata.chunk_size} chars | "
            f"Strategy: {chunk_metadata.chunk_strategy} | "
            f"Time: {chunk_metadata.processing_time:.3f}s",
            extra={
                'chunk_metadata': asdict(chunk_metadata),
                'operation_type': 'chunk_processing'
            }
        )
    
    def log_rag_operation(self, rag_metrics: RAGOperationMetrics):
        """Log comprehensive RAG operation metrics"""
        status = "✅ SUCCESS" if rag_metrics.success else "❌ FAILED"
        
        rag_logger.info(
            f"🧠 RAG Operation {status} | "
            f"ID: {rag_metrics.operation_id} | "
            f"Query: '{rag_metrics.query[:50]}...' | "
            f"Contexts: {len(rag_metrics.contexts_searched)} | "
            f"Chunks: {rag_metrics.total_chunks_retrieved} | "
            f"Response Time: {rag_metrics.total_response_time:.3f}s | "
            f"Tokens: {rag_metrics.tokens_input}→{rag_metrics.tokens_output}",
            extra={
                'rag_metrics': asdict(rag_metrics),
                'operation_type': 'rag_operation'
            }
        )
        
        # Log detailed breakdown
        rag_logger.debug(
            f"RAG Breakdown - Retrieval: {rag_metrics.retrieval_time:.3f}s | "
            f"Generation: {rag_metrics.llm_generation_time:.3f}s | "
            f"Model: {rag_metrics.model_used} | "
            f"Response Length: {rag_metrics.response_length}",
            extra={
                'operation_id': rag_metrics.operation_id,
                'performance_breakdown': {
                    'retrieval_time': rag_metrics.retrieval_time,
                    'generation_time': rag_metrics.llm_generation_time,
                    'total_time': rag_metrics.total_response_time
                }
            }
        )
    
    def log_vector_operation(self, vector_log: VectorOperationLog):
        """Log vector store operations"""
        status = "✅" if vector_log.success else "❌"
        
        vector_logger.info(
            f"🔍 Vector {vector_log.operation_type.upper()} {status} | "
            f"ID: {vector_log.operation_id} | "
            f"Context: {vector_log.context_id} | "
            f"Model: {vector_log.embedding_model} | "
            f"Time: {vector_log.operation_time:.3f}s" +
            (f" | Chunks: {vector_log.chunks_processed}" if vector_log.chunks_processed else "") +
            (f" | Results: {vector_log.results_count}" if vector_log.results_count else ""),
            extra={
                'vector_operation': asdict(vector_log),
                'operation_type': 'vector_operation'
            }
        )
    
    def log_context_creation(self, context_log: ContextCreationLog):
        """Log context creation and management"""
        status = "✅ SUCCESS" if context_log.success else "❌ FAILED"
        
        context_logger.info(
            f"📚 Context Creation {status} | "
            f"ID: {context_log.context_id} | "
            f"Name: '{context_log.context_name}' | "
            f"Type: {context_log.context_type} | "
            f"Sources: {len(context_log.sources)} | "
            f"Files: {context_log.total_files} | "
            f"Size: {context_log.total_size_bytes:,} bytes | "
            f"Chunks: {context_log.chunks_created} | "
            f"Time: {context_log.processing_time:.3f}s",
            extra={
                'context_creation': asdict(context_log),
                'operation_type': 'context_creation'
            }
        )
        
        # Log source details
        for i, source in enumerate(context_log.sources):
            context_logger.debug(
                f"📁 Source {i+1}: {source.get('type', 'unknown')} | "
                f"Location: {source.get('location', 'N/A')} | "
                f"Files: {source.get('file_count', 0)}",
                extra={
                    'context_id': context_log.context_id,
                    'source_details': source,
                    'operation_type': 'context_source'
                }
            )
    
    def log_llm_interaction(self, operation_id: str, model: str, input_tokens: int, 
                           output_tokens: int, response_time: float, prompt_type: str = "chat"):
        """Log LLM interaction details"""
        llm_logger.info(
            f"🤖 LLM Interaction | "
            f"ID: {operation_id} | "
            f"Model: {model} | "
            f"Type: {prompt_type} | "
            f"Tokens: {input_tokens}→{output_tokens} | "
            f"Time: {response_time:.3f}s | "
            f"Rate: {output_tokens/response_time:.1f} tokens/s",
            extra={
                'operation_id': operation_id,
                'model': model,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'response_time': response_time,
                'tokens_per_second': output_tokens/response_time,
                'prompt_type': prompt_type,
                'operation_type': 'llm_interaction'
            }
        )
    
    def log_user_activity(self, user_id: int, session_id: int, activity_type: str, 
                         details: Dict[str, Any]):
        """Log user activity and session information"""
        user_activity_logger.info(
            f"👤 User Activity | "
            f"User: {user_id} | "
            f"Session: {session_id} | "
            f"Activity: {activity_type}",
            extra={
                'user_id': user_id,
                'session_id': session_id,
                'activity_type': activity_type,
                'activity_details': details,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'operation_type': 'user_activity'
            }
        )
    
    def log_performance_summary(self, operation_id: str, metrics: Dict[str, Any]):
        """Log performance summary for complex operations"""
        performance_logger.info(
            f"📊 Performance Summary | ID: {operation_id}",
            extra={
                'operation_id': operation_id,
                'performance_metrics': metrics,
                'operation_type': 'performance_summary'
            }
        )
    
    def get_session_metrics(self, session_id: int) -> Dict[str, Any]:
        """Get aggregated metrics for a session"""
        return self.session_metrics.get(session_id, {})
    
    def update_session_metrics(self, session_id: int, metrics: Dict[str, Any]):
        """Update session-level metrics"""
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = {}
        
        self.session_metrics[session_id].update(metrics)

# Global instance
detailed_logger = DetailedLogger()

# Convenience functions
def log_chunk_processing(chunk_metadata: ChunkMetadata):
    """Convenience function for chunk logging"""
    detailed_logger.log_chunk_processing(chunk_metadata)

def log_rag_operation(rag_metrics: RAGOperationMetrics):
    """Convenience function for RAG logging"""
    detailed_logger.log_rag_operation(rag_metrics)

def log_vector_operation(vector_log: VectorOperationLog):
    """Convenience function for vector logging"""
    detailed_logger.log_vector_operation(vector_log)

def log_context_creation(context_log: ContextCreationLog):
    """Convenience function for context logging"""
    detailed_logger.log_context_creation(context_log)

def track_operation(operation_name: str, **kwargs):
    """Convenience function for operation tracking"""
    return detailed_logger.track_operation(operation_name, **kwargs)