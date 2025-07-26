"""
Context cleanup service for comprehensive data removal
"""

import os
import shutil
import json
from typing import List, Dict, Any
from flask import current_app
from services.vector_service import VectorService


class ContextCleanupService:
    """Service for comprehensive context cleanup and data removal"""
    
    def __init__(self):
        self.cleanup_stats = {
            'vector_stores_deleted': 0,
            'documents_deleted': 0,
            'files_deleted': 0,
            'messages_cleaned': 0,
            'chat_sessions_cleaned': 0,
            'chunks_deleted': 0,
            'errors': []
        }
    
    def delete_context_completely(self, context_id: int, user_id: int) -> Dict[str, Any]:
        """
        Completely delete a context and all associated data

        Args:
            context_id: ID of the context to delete
            user_id: ID of the user (for security verification)

        Returns:
            Dictionary with cleanup statistics and any errors
        """
        try:
            # Get db and models from current app context
            from flask_sqlalchemy import SQLAlchemy
            db = current_app.extensions['sqlalchemy']

            # Import models dynamically to avoid circular imports
            from models import Context, Document, Message, ChatSession

            # Reset cleanup stats
            self.cleanup_stats = {
                'vector_stores_deleted': 0,
                'documents_deleted': 0,
                'files_deleted': 0,
                'messages_cleaned': 0,
                'chat_sessions_cleaned': 0,
                'chunks_deleted': 0,
                'errors': []
            }

            # Get context and verify ownership
            context = db.session.get(Context, context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            if context.user_id != user_id:
                raise ValueError(f"Context {context_id} does not belong to user {user_id}")
            
            print(f"Starting complete cleanup for context {context_id}: {context.name}")
            
            # 1. Clean up vector stores and embeddings
            self._cleanup_vector_stores(context)
            
            # 2. Clean up uploaded files and documents
            self._cleanup_files_and_documents(context)
            
            # 3. Clean up text chunks (for app_local.py)
            self._cleanup_text_chunks(context_id)
            
            # 4. Clean up chat messages and sessions
            self._cleanup_chat_data(context_id)
            
            # 5. Clean up context versions (if using versioning)
            self._cleanup_context_versions(context_id)
            
            # 6. Clean up repository clones (if any)
            self._cleanup_repository_files(context)
            
            # 7. Finally delete the context itself
            db.session.delete(context)
            db.session.commit()
            
            print(f"Context {context_id} cleanup completed successfully")
            
            return {
                'success': True,
                'message': f'Context "{context.name}" and all associated data deleted successfully',
                'stats': self.cleanup_stats
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error during context cleanup: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'stats': self.cleanup_stats
            }
    
    def _cleanup_vector_stores(self, context: Context):
        """Clean up vector stores and embeddings"""
        try:
            if context.vector_store_path and os.path.exists(context.vector_store_path):
                # Use VectorService to properly delete the vector store
                vector_service = VectorService()
                if vector_service.delete_vector_store(context.vector_store_path):
                    self.cleanup_stats['vector_stores_deleted'] += 1
                    print(f"Deleted vector store: {context.vector_store_path}")
                else:
                    self.cleanup_stats['errors'].append(f"Failed to delete vector store: {context.vector_store_path}")
            
            # Also check for any vector stores with the context ID pattern
            vector_store_base = os.path.join('vector_store', f'context_{context.id}')
            if os.path.exists(vector_store_base):
                shutil.rmtree(vector_store_base)
                self.cleanup_stats['vector_stores_deleted'] += 1
                print(f"Deleted vector store directory: {vector_store_base}")
                
        except Exception as e:
            error_msg = f"Error cleaning up vector stores: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
    
    def _cleanup_files_and_documents(self, context: Context):
        """Clean up uploaded files and document records"""
        try:
            # Get all documents for this context
            documents = Document.query.filter_by(context_id=context.id).all()
            
            for document in documents:
                try:
                    # Delete physical file if it exists
                    if document.file_path and os.path.exists(document.file_path):
                        os.remove(document.file_path)
                        self.cleanup_stats['files_deleted'] += 1
                        print(f"Deleted file: {document.file_path}")
                    
                    # Delete document record
                    db.session.delete(document)
                    self.cleanup_stats['documents_deleted'] += 1
                    
                except Exception as e:
                    error_msg = f"Error deleting document {document.filename}: {str(e)}"
                    print(error_msg)
                    self.cleanup_stats['errors'].append(error_msg)
            
            # Clean up context-specific upload directory
            upload_dir = os.path.join('uploads', f'context_{context.id}')
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
                print(f"Deleted upload directory: {upload_dir}")
                
        except Exception as e:
            error_msg = f"Error cleaning up files and documents: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
    
    def _cleanup_text_chunks(self, context_id: int):
        """Clean up text chunks (for app_local.py TextChunk model)"""
        try:
            # Check if TextChunk model exists (for app_local.py)
            try:
                from app_local import TextChunk
                chunks = TextChunk.query.filter_by(context_id=context_id).all()
                chunk_count = len(chunks)
                
                for chunk in chunks:
                    db.session.delete(chunk)
                
                self.cleanup_stats['chunks_deleted'] = chunk_count
                print(f"Deleted {chunk_count} text chunks")
                
            except ImportError:
                # TextChunk model doesn't exist in this setup
                pass
                
        except Exception as e:
            error_msg = f"Error cleaning up text chunks: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
    
    def _cleanup_chat_data(self, context_id: int):
        """Clean up chat messages and sessions that reference this context"""
        try:
            # Find all messages that reference this context
            messages = Message.query.all()
            messages_to_update = []
            messages_to_delete = []
            
            for message in messages:
                context_ids = message.get_context_ids()
                if context_id in context_ids:
                    # Remove this context from the message's context list
                    updated_context_ids = [cid for cid in context_ids if cid != context_id]
                    
                    if updated_context_ids:
                        # Message still has other contexts, just update it
                        message.set_context_ids(updated_context_ids)
                        messages_to_update.append(message)
                    else:
                        # Message only referenced this context, delete it
                        messages_to_delete.append(message)
            
            # Update messages that still have other contexts
            for message in messages_to_update:
                self.cleanup_stats['messages_cleaned'] += 1
            
            # Delete messages that only referenced this context
            for message in messages_to_delete:
                db.session.delete(message)
                self.cleanup_stats['messages_cleaned'] += 1
            
            # Check for empty chat sessions and clean them up
            sessions = ChatSession.query.all()
            for session in sessions:
                if len(session.messages) == 0:
                    db.session.delete(session)
                    self.cleanup_stats['chat_sessions_cleaned'] += 1
            
            print(f"Cleaned up {self.cleanup_stats['messages_cleaned']} messages and {self.cleanup_stats['chat_sessions_cleaned']} empty sessions")
            
        except Exception as e:
            error_msg = f"Error cleaning up chat data: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
    
    def _cleanup_context_versions(self, context_id: int):
        """Clean up context versions if versioning is enabled"""
        try:
            # Check if context versioning is available
            try:
                from models.context_version import ContextVersion
                versions = ContextVersion.query.filter_by(context_id=context_id).all()
                
                for version in versions:
                    db.session.delete(version)
                
                print(f"Deleted {len(versions)} context versions")
                
            except ImportError:
                # Context versioning not available
                pass
                
        except Exception as e:
            error_msg = f"Error cleaning up context versions: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
    
    def _cleanup_repository_files(self, context: Context):
        """Clean up cloned repository files"""
        try:
            if context.source_type == 'repo':
                config = context.get_config()
                
                # Clean up any temporary repository clones
                temp_dirs = [
                    f'/tmp/rag_repos/context_{context.id}',
                    f'temp/repos/context_{context.id}',
                    f'repos/context_{context.id}'
                ]
                
                for temp_dir in temp_dirs:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        print(f"Deleted repository clone: {temp_dir}")
                        
        except Exception as e:
            error_msg = f"Error cleaning up repository files: {str(e)}"
            print(error_msg)
            self.cleanup_stats['errors'].append(error_msg)
    
    def cleanup_orphaned_data(self) -> Dict[str, Any]:
        """Clean up orphaned data across the system"""
        try:
            cleanup_stats = {
                'orphaned_vector_stores': 0,
                'orphaned_files': 0,
                'orphaned_messages': 0,
                'errors': []
            }
            
            # Find orphaned vector stores
            vector_store_dir = 'vector_store'
            if os.path.exists(vector_store_dir):
                for item in os.listdir(vector_store_dir):
                    if item.startswith('context_'):
                        context_id = int(item.split('_')[1])
                        context = db.session.get(Context, context_id)
                        if not context:
                            # Orphaned vector store
                            orphaned_path = os.path.join(vector_store_dir, item)
                            shutil.rmtree(orphaned_path)
                            cleanup_stats['orphaned_vector_stores'] += 1
            
            # Find orphaned upload directories
            uploads_dir = 'uploads'
            if os.path.exists(uploads_dir):
                for item in os.listdir(uploads_dir):
                    if item.startswith('context_'):
                        context_id = int(item.split('_')[1])
                        context = db.session.get(Context, context_id)
                        if not context:
                            # Orphaned upload directory
                            orphaned_path = os.path.join(uploads_dir, item)
                            shutil.rmtree(orphaned_path)
                            cleanup_stats['orphaned_files'] += 1
            
            return {
                'success': True,
                'message': 'Orphaned data cleanup completed',
                'stats': cleanup_stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stats': cleanup_stats
            }
