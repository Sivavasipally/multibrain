"""
Task Handlers for Background Processing System

This module contains the actual task handler functions that execute different
types of background tasks in the RAG Chatbot PWA system. Each handler is 
responsible for a specific type of operation and can be executed asynchronously.

Task Handler Types:
- document_processing: Process uploaded documents
- context_reprocessing: Reprocess existing contexts
- version_creation: Create context versions
- repository_cloning: Clone and process repositories
- cleanup_operations: System maintenance tasks

Handler Interface:
    def handler_function(task: Task) -> Any:
        # Access task parameters via task.args
        # Update task progress via task callback if needed
        # Return result data

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# Import Flask app context for database operations
from flask import current_app

# Import services and models
from services.document_processor import DocumentProcessor
from services.vector_service import VectorService
from services.repository_service import RepositoryService
from database import db
from models import Context, Document, User
from context_versioning import ContextVersionService

# Import logging
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('task_handlers')

def document_processing_handler(task) -> Dict[str, Any]:
    """
    Handler for document processing tasks
    
    Processes uploaded documents for a context by extracting text,
    creating chunks, and building vector indexes for search.
    
    Args:
        task: Task object with args containing:
            - context_id: ID of context to process
            - force_reprocess: Whether to reprocess existing documents
            
    Returns:
        Dict with processing results and statistics
    """
    logger.info(f"Starting document processing task {task.id}")
    
    context_id = task.args.get('context_id')
    force_reprocess = task.args.get('force_reprocess', False)
    
    if not context_id:
        raise ValueError("context_id is required for document processing")
    
    # Use Flask app context for database operations
    with current_app.app_context():
        try:
            # Get the context
            context = Context.query.get(context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            logger.info(f"Processing documents for context: {context.name}")
            
            # Update task progress
            task.progress = 10
            
            # Update context status
            context.status = 'processing'
            context.progress = 10
            db.session.commit()
            
            # Get documents to process
            query = Document.query.filter_by(context_id=context_id)
            if not force_reprocess:
                # Only process documents that haven't been processed yet
                query = query.filter_by(processed_at=None)
            
            documents = query.all()
            logger.info(f"Found {len(documents)} documents to process")
            
            if not documents:
                return {
                    'message': 'No documents to process',
                    'processed_count': 0,
                    'total_chunks': 0,
                    'total_tokens': 0
                }
            
            # Initialize services
            doc_processor = DocumentProcessor()
            vector_service = VectorService()
            
            # Process documents
            all_chunks = []
            total_tokens = 0
            processed_count = 0
            
            for i, document in enumerate(documents):
                try:
                    logger.info(f"Processing document {i+1}/{len(documents)}: {document.filename}")
                    
                    # Update progress
                    progress = 10 + (i / len(documents)) * 70
                    task.progress = int(progress)
                    context.progress = int(progress)
                    db.session.commit()
                    
                    # Process the document
                    if document.file_path and os.path.exists(document.file_path):
                        chunks = doc_processor.process_file(
                            document.file_path,
                            context.chunk_strategy or 'language-specific'
                        )
                        
                        # Save chunks to database
                        for chunk_index, chunk in enumerate(chunks):
                            from models import TextChunk
                            
                            text_chunk = TextChunk(
                                context_id=context_id,
                                file_name=document.filename,
                                chunk_index=chunk_index,
                                content=chunk['content']
                            )
                            
                            # Set file info if available
                            if 'metadata' in chunk:
                                text_chunk.set_file_info(chunk['metadata'])
                            
                            db.session.add(text_chunk)
                            all_chunks.append(chunk)
                        
                        # Update document statistics
                        document.chunks_count = len(chunks)
                        document.tokens_count = sum(len(chunk['content'].split()) for chunk in chunks)
                        document.processed_at = datetime.now(timezone.utc)
                        
                        total_tokens += document.tokens_count
                        processed_count += 1
                        
                        logger.info(f"Processed {document.filename}: {len(chunks)} chunks, {document.tokens_count} tokens")
                        
                    else:
                        logger.warning(f"File not found for document {document.id}: {document.file_path}")
                        
                except Exception as doc_error:
                    logger.error(f"Error processing document {document.filename}: {doc_error}")
                    # Continue processing other documents
                    continue
            
            # Update task progress
            task.progress = 80
            context.progress = 80
            db.session.commit()
            
            # Create vector store if we have chunks
            vector_store_path = None
            if all_chunks:
                try:
                    # Create vector store directory
                    vector_store_dir = os.path.join('vector_stores', f'context_{context_id}')
                    os.makedirs(vector_store_dir, exist_ok=True)
                    
                    logger.info(f"Creating vector store with {len(all_chunks)} chunks")
                    vector_service.create_vector_store(all_chunks, vector_store_dir)
                    
                    context.vector_store_path = vector_store_dir
                    vector_store_path = vector_store_dir
                    
                except Exception as vector_error:
                    logger.error(f"Failed to create vector store: {vector_error}")
                    # Continue without vector store
            
            # Update context final statistics
            context.total_chunks = len(all_chunks)
            context.total_tokens = total_tokens
            context.status = 'ready'
            context.progress = 100
            
            # Create automatic version
            try:
                changes = {
                    'document_processing': {
                        'operation': 'processed',
                        'description': f'Processed {processed_count} documents',
                        'impact_score': min(processed_count, 10),
                        'documents_processed': processed_count,
                        'chunks_created': len(all_chunks),
                        'tokens_processed': total_tokens
                    }
                }
                
                version = ContextVersionService.create_version(
                    context=context,
                    user_id=task.user_id,
                    description=f"Auto-version after background processing of {processed_count} documents",
                    version_type='auto',
                    changes=changes,
                    force_major=processed_count >= 5
                )
                
                logger.info(f"Created automatic version {version.version_number}")
                
            except Exception as version_error:
                logger.warning(f"Failed to create automatic version: {version_error}")
            
            # Final commit
            db.session.commit()
            
            # Update final task progress
            task.progress = 100
            
            result = {
                'message': f'Successfully processed {processed_count} documents',
                'processed_count': processed_count,
                'total_chunks': len(all_chunks),
                'total_tokens': total_tokens,
                'vector_store_path': vector_store_path,
                'context_status': 'ready'
            }
            
            logger.info(f"Document processing completed: {result}")
            return result
            
        except Exception as e:
            # Update context status on error
            if 'context' in locals():
                context.status = 'error'
                context.error_message = str(e)
                db.session.commit()
            
            logger.error(f"Document processing failed: {e}")
            raise

def context_reprocessing_handler(task) -> Dict[str, Any]:
    """
    Handler for context reprocessing tasks
    
    Reprocesses all documents in a context, useful for applying new
    chunking strategies or updating embeddings.
    
    Args:
        task: Task object with args containing:
            - context_id: ID of context to reprocess
            - new_chunk_strategy: Optional new chunking strategy
            - clear_existing: Whether to clear existing chunks
            
    Returns:
        Dict with reprocessing results
    """
    logger.info(f"Starting context reprocessing task {task.id}")
    
    context_id = task.args.get('context_id')
    new_chunk_strategy = task.args.get('new_chunk_strategy')
    clear_existing = task.args.get('clear_existing', True)
    
    if not context_id:
        raise ValueError("context_id is required for context reprocessing")
    
    with current_app.app_context():
        context = Context.query.get(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        logger.info(f"Reprocessing context: {context.name}")
        
        # Update chunk strategy if provided
        if new_chunk_strategy:
            context.chunk_strategy = new_chunk_strategy
            db.session.commit()
        
        # Clear existing chunks if requested
        if clear_existing:
            from models import TextChunk
            TextChunk.query.filter_by(context_id=context_id).delete()
            db.session.commit()
            logger.info("Cleared existing text chunks")
        
        # Reset document processing status
        Document.query.filter_by(context_id=context_id).update({
            'processed_at': None,
            'chunks_count': 0,
            'tokens_count': 0
        })
        db.session.commit()
        
        # Process documents using the document processing handler
        processing_task_args = {
            'context_id': context_id,
            'force_reprocess': True
        }
        
        # Create a temporary task object for the handler
        from services.task_service import Task, TaskStatus, TaskPriority
        temp_task = Task(
            id=task.id + "_reprocess",
            task_type='document_processing',
            handler='document_processing',
            args=processing_task_args,
            priority=TaskPriority.NORMAL,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(timezone.utc),
            user_id=task.user_id,
            context_id=context_id
        )
        
        result = document_processing_handler(temp_task)
        
        return {
            'message': f'Successfully reprocessed context "{context.name}"',
            'context_id': context_id,
            'processing_result': result
        }

def version_creation_handler(task) -> Dict[str, Any]:
    """
    Handler for version creation tasks
    
    Creates versions for contexts, useful for scheduled versioning
    or batch version operations.
    
    Args:
        task: Task object with args containing:
            - context_id: ID of context to version
            - description: Version description
            - version_type: Type of version (manual, milestone, etc.)
            - force_major: Whether to force major version
            
    Returns:
        Dict with version creation results
    """
    logger.info(f"Starting version creation task {task.id}")
    
    context_id = task.args.get('context_id')
    description = task.args.get('description', 'Scheduled version creation')
    version_type = task.args.get('version_type', 'auto')
    force_major = task.args.get('force_major', False)
    
    if not context_id:
        raise ValueError("context_id is required for version creation")
    
    with current_app.app_context():
        context = Context.query.get(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        logger.info(f"Creating version for context: {context.name}")
        
        changes = {
            'scheduled_version': {
                'operation': 'version_created',
                'description': 'Scheduled version creation via background task',
                'impact_score': 3
            }
        }
        
        version = ContextVersionService.create_version(
            context=context,
            user_id=task.user_id,
            description=description,
            version_type=version_type,
            changes=changes,
            force_major=force_major
        )
        
        return {
            'message': f'Successfully created version {version.version_number}',
            'version_id': version.id,
            'version_number': version.version_number,
            'context_id': context_id
        }

def repository_cloning_handler(task) -> Dict[str, Any]:
    """
    Handler for repository cloning and processing tasks
    
    Clones a repository and processes its files as a background task.
    
    Args:
        task: Task object with args containing:
            - context_id: ID of context for the repository
            - repo_url: Repository URL to clone
            - branch: Branch to clone (optional)
            - access_token: Access token for private repos (optional)
            
    Returns:
        Dict with cloning and processing results
    """
    logger.info(f"Starting repository cloning task {task.id}")
    
    context_id = task.args.get('context_id')
    repo_url = task.args.get('repo_url')
    branch = task.args.get('branch', 'main')
    access_token = task.args.get('access_token')
    
    if not context_id or not repo_url:
        raise ValueError("context_id and repo_url are required for repository cloning")
    
    with current_app.app_context():
        try:
            context = Context.query.get(context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            logger.info(f"Cloning repository {repo_url} for context: {context.name}")
            
            # Update context status
            context.status = 'processing'
            context.progress = 10
            db.session.commit()
            
            # Initialize repository service
            repo_service = RepositoryService()
            
            # Create temporary directory for cloning
            with tempfile.TemporaryDirectory() as temp_dir:
                clone_path = os.path.join(temp_dir, 'repo')
                
                # Update progress
                task.progress = 20
                context.progress = 20
                db.session.commit()
                
                # Clone repository
                repo_service.clone_repository(repo_url, clone_path, branch, access_token)
                logger.info(f"Repository cloned to {clone_path}")
                
                # Update progress
                task.progress = 40
                context.progress = 40
                db.session.commit()
                
                # Process repository files
                result = repo_service.process_repository_files(
                    clone_path, context_id, task.user_id
                )
                
                # Update progress
                task.progress = 80
                context.progress = 80
                db.session.commit()
                
                # Process documents (same as document processing)
                processing_result = document_processing_handler(task)
                
                # Combine results
                combined_result = {
                    'message': f'Successfully cloned and processed repository {repo_url}',
                    'repository_url': repo_url,
                    'branch': branch,
                    'files_processed': result.get('files_processed', 0),
                    'processing_result': processing_result
                }
                
                logger.info(f"Repository processing completed: {combined_result}")
                return combined_result
                
        except Exception as e:
            # Update context status on error
            if 'context' in locals():
                context.status = 'error'
                context.error_message = str(e)
                db.session.commit()
            
            logger.error(f"Repository cloning failed: {e}")
            raise

def cleanup_operations_handler(task) -> Dict[str, Any]:
    """
    Handler for system cleanup and maintenance tasks
    
    Performs various cleanup operations like removing old files,
    optimizing databases, clearing caches, etc.
    
    Args:
        task: Task object with args containing:
            - operation_type: Type of cleanup operation
            - max_age_days: Maximum age for cleanup (optional)
            - dry_run: Whether to perform dry run (optional)
            
    Returns:
        Dict with cleanup results
    """
    logger.info(f"Starting cleanup operations task {task.id}")
    
    operation_type = task.args.get('operation_type', 'general')
    max_age_days = task.args.get('max_age_days', 30)
    dry_run = task.args.get('dry_run', False)
    
    logger.info(f"Performing {operation_type} cleanup (dry_run: {dry_run})")
    
    cleanup_results = {
        'operation_type': operation_type,
        'dry_run': dry_run,
        'items_processed': 0,
        'items_removed': 0,
        'space_freed_mb': 0,
        'operations': []
    }
    
    with current_app.app_context():
        try:
            if operation_type in ['general', 'temp_files']:
                # Clean up temporary files
                temp_result = _cleanup_temp_files(max_age_days, dry_run)
                cleanup_results['operations'].append(temp_result)
                cleanup_results['items_removed'] += temp_result.get('files_removed', 0)
                cleanup_results['space_freed_mb'] += temp_result.get('space_freed_mb', 0)
                task.progress = 25
            
            if operation_type in ['general', 'old_uploads']:
                # Clean up old upload files
                upload_result = _cleanup_old_uploads(max_age_days, dry_run)
                cleanup_results['operations'].append(upload_result)
                cleanup_results['items_removed'] += upload_result.get('files_removed', 0)
                cleanup_results['space_freed_mb'] += upload_result.get('space_freed_mb', 0)
                task.progress = 50
            
            if operation_type in ['general', 'orphaned_chunks']:
                # Clean up orphaned text chunks
                chunk_result = _cleanup_orphaned_chunks(dry_run)
                cleanup_results['operations'].append(chunk_result)
                cleanup_results['items_removed'] += chunk_result.get('chunks_removed', 0)
                task.progress = 75
            
            if operation_type in ['general', 'old_versions']:
                # Clean up old versions (keep protected ones)
                version_result = _cleanup_old_versions(max_age_days, dry_run)
                cleanup_results['operations'].append(version_result)
                cleanup_results['items_removed'] += version_result.get('versions_removed', 0)
                task.progress = 90
            
            task.progress = 100
            
            cleanup_results['message'] = f"Cleanup completed: removed {cleanup_results['items_removed']} items, freed {cleanup_results['space_freed_mb']:.2f} MB"
            
            logger.info(f"Cleanup operations completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Cleanup operations failed: {e}")
            raise

def _cleanup_temp_files(max_age_days: int, dry_run: bool) -> Dict[str, Any]:
    """Clean up temporary files"""
    import tempfile
    
    temp_dir = tempfile.gettempdir()
    cutoff_time = time.time() - (max_age_days * 24 * 3600)
    
    files_removed = 0
    space_freed = 0
    
    try:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        if not dry_run:
                            os.remove(file_path)
                        files_removed += 1
                        space_freed += file_size
                except (OSError, IOError):
                    continue  # Skip files we can't access
                    
    except Exception as e:
        logger.warning(f"Error during temp file cleanup: {e}")
    
    return {
        'operation': 'temp_files',
        'files_removed': files_removed,
        'space_freed_mb': space_freed / (1024 * 1024),
        'dry_run': dry_run
    }

def _cleanup_old_uploads(max_age_days: int, dry_run: bool) -> Dict[str, Any]:
    """Clean up old upload files"""
    uploads_dir = 'uploads'
    
    if not os.path.exists(uploads_dir):
        return {'operation': 'old_uploads', 'files_removed': 0, 'space_freed_mb': 0}
    
    cutoff_time = time.time() - (max_age_days * 24 * 3600)
    files_removed = 0
    space_freed = 0
    
    try:
        for root, dirs, files in os.walk(uploads_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        # Check if file is still referenced in database
                        with current_app.app_context():
                            doc = Document.query.filter_by(file_path=file_path).first()
                            if not doc:  # File not in database, safe to remove
                                file_size = os.path.getsize(file_path)
                                if not dry_run:
                                    os.remove(file_path)
                                files_removed += 1
                                space_freed += file_size
                                
                except (OSError, IOError):
                    continue
                    
    except Exception as e:
        logger.warning(f"Error during upload cleanup: {e}")
    
    return {
        'operation': 'old_uploads',
        'files_removed': files_removed,
        'space_freed_mb': space_freed / (1024 * 1024),
        'dry_run': dry_run
    }

def _cleanup_orphaned_chunks(dry_run: bool) -> Dict[str, Any]:
    """Clean up orphaned text chunks"""
    from models import TextChunk, Context
    
    # Find chunks with non-existent contexts
    orphaned_chunks = db.session.query(TextChunk).filter(
        ~TextChunk.context_id.in_(
            db.session.query(Context.id)
        )
    ).all()
    
    chunks_removed = len(orphaned_chunks)
    
    if not dry_run and orphaned_chunks:
        for chunk in orphaned_chunks:
            db.session.delete(chunk)
        db.session.commit()
    
    return {
        'operation': 'orphaned_chunks',
        'chunks_removed': chunks_removed,
        'dry_run': dry_run
    }

def _cleanup_old_versions(max_age_days: int, dry_run: bool) -> Dict[str, Any]:
    """Clean up old unprotected versions"""
    from context_versioning import ContextVersion
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    
    # Find old, unprotected, non-current versions
    old_versions = ContextVersion.query.filter(
        ContextVersion.created_at < cutoff_date,
        ContextVersion.is_protected == False,
        ContextVersion.is_current == False
    ).all()
    
    versions_removed = len(old_versions)
    
    if not dry_run and old_versions:
        for version in old_versions:
            db.session.delete(version)
        db.session.commit()
    
    return {
        'operation': 'old_versions',
        'versions_removed': versions_removed,
        'dry_run': dry_run
    }