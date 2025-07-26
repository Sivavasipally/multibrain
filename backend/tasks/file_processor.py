"""
Celery tasks for file processing
"""

import os
from datetime import datetime, timezone
from celery import current_app
from app import celery
from models import db, Context, Document
from services.document_processor import DocumentProcessor
from services.vector_service import VectorService

@celery.task(bind=True)
def process_uploaded_files_task(self, context_id: int):
    """Process uploaded files for a context"""
    try:
        # Get context from database
        context = db.session.get(Context, context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        # Update status
        context.status = 'processing'
        context.progress = 0
        db.session.commit()
        
        # Get unprocessed documents
        documents = Document.query.filter_by(
            context_id=context_id,
            processed_at=None
        ).all()
        
        if not documents:
            return f"No new files to process for context {context_id}"
        
        # Update progress
        context.progress = 10
        db.session.commit()
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Starting file processing'})
        
        # Process files
        document_processor = DocumentProcessor()
        all_chunks = []
        
        total_files = len(documents)
        processed_files = 0
        
        for document in documents:
            try:
                if not os.path.exists(document.file_path):
                    print(f"File not found: {document.file_path}")
                    continue
                
                # Process file
                chunks = document_processor.process_file(document.file_path, context.chunk_strategy)
                
                # Update chunk metadata
                for chunk in chunks:
                    chunk['metadata']['document_id'] = document.id
                    chunk['metadata']['upload_filename'] = document.filename
                    chunk['metadata']['context_id'] = context_id
                
                all_chunks.extend(chunks)
                
                # Update document with processing info
                document.chunks_count = len(chunks)
                document.tokens_count = sum(len(chunk['content']) // 4 for chunk in chunks)
                document.processed_at = datetime.now(timezone.utc)
                
                processed_files += 1
                
                # Update progress
                progress = 10 + int((processed_files / total_files) * 60)
                context.progress = progress
                db.session.commit()
                self.update_state(state='PROGRESS', meta={
                    'progress': progress, 
                    'status': f'Processed {processed_files}/{total_files} files'
                })
            
            except Exception as e:
                print(f"Error processing file {document.filename}: {e}")
                # Mark document as having an error but continue processing others
                document.processed_at = datetime.now(timezone.utc)
                continue
        
        # Update progress
        context.progress = 70
        db.session.commit()
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Updating vector store'})
        
        # Update or create vector store
        if all_chunks:
            vector_service = VectorService(context.embedding_model)
            vector_store_path = os.path.join('vector_store', f'context_{context.id}')
            
            # Check if vector store already exists
            if context.vector_store_path and os.path.exists(context.vector_store_path):
                # Add new chunks to existing store
                vector_service.add_chunks_to_store(context.vector_store_path, all_chunks)
            else:
                # Create new vector store
                vector_service.create_vector_store(all_chunks, vector_store_path)
                context.vector_store_path = vector_store_path
            
            # Update context statistics
            context.total_chunks = (context.total_chunks or 0) + len(all_chunks)
            context.total_tokens = (context.total_tokens or 0) + sum(len(chunk['content']) // 4 for chunk in all_chunks)
        
        # Mark as ready
        context.status = 'ready'
        context.progress = 100
        db.session.commit()
        
        return f"Successfully processed {processed_files} files for context {context_id}"
    
    except Exception as e:
        # Mark as error
        context = db.session.get(Context, context_id)
        if context:
            context.status = 'error'
            context.error_message = str(e)
            db.session.commit()
        
        raise e

@celery.task(bind=True)
def reprocess_context_files_task(self, context_id: int):
    """Reprocess all files for a context"""
    try:
        # Get context from database
        context = db.session.get(Context, context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        # Update status
        context.status = 'processing'
        context.progress = 0
        context.error_message = None
        db.session.commit()
        
        # Get all documents for this context
        documents = Document.query.filter_by(context_id=context_id).all()
        
        if not documents:
            context.status = 'ready'
            context.progress = 100
            db.session.commit()
            return f"No files found for context {context_id}"
        
        # Reset document processing status
        for document in documents:
            document.processed_at = None
            document.chunks_count = 0
            document.tokens_count = 0
        
        # Clear existing vector store
        if context.vector_store_path and os.path.exists(context.vector_store_path):
            import shutil
            shutil.rmtree(context.vector_store_path)
        
        # Reset context statistics
        context.total_chunks = 0
        context.total_tokens = 0
        context.vector_store_path = None
        
        db.session.commit()
        
        # Process all files
        return process_uploaded_files_task.apply_async(args=[context_id]).get()
    
    except Exception as e:
        # Mark as error
        context = db.session.get(Context, context_id)
        if context:
            context.status = 'error'
            context.error_message = str(e)
            db.session.commit()
        
        raise e

@celery.task(bind=True)
def cleanup_orphaned_files_task(self):
    """Clean up orphaned files that are no longer referenced"""
    try:
        cleaned_count = 0
        
        # Get all document file paths
        documents = Document.query.all()
        referenced_paths = {doc.file_path for doc in documents}
        
        # Check upload directories
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        
        if os.path.exists(upload_folder):
            for root, dirs, files in os.walk(upload_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # If file is not referenced by any document, delete it
                    if file_path not in referenced_paths:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            print(f"Error deleting orphaned file {file_path}: {e}")
        
        return f"Cleaned up {cleaned_count} orphaned files"
    
    except Exception as e:
        return f"Error during cleanup: {str(e)}"

@celery.task(bind=True)
def optimize_vector_stores_task(self):
    """Optimize vector stores by rebuilding them"""
    try:
        optimized_count = 0
        
        # Get all contexts with vector stores
        contexts = Context.query.filter(
            Context.vector_store_path.isnot(None),
            Context.status == 'ready'
        ).all()
        
        for context in contexts:
            try:
                if not os.path.exists(context.vector_store_path):
                    continue
                
                # Load existing vector store
                vector_service = VectorService(context.embedding_model)
                index, metadata = vector_service.load_vector_store(context.vector_store_path)
                
                # Rebuild vector store (this can help with performance)
                chunks = metadata['chunks']
                if chunks:
                    # Create backup
                    backup_path = context.vector_store_path + '_backup'
                    import shutil
                    shutil.copytree(context.vector_store_path, backup_path)
                    
                    try:
                        # Rebuild
                        vector_service.create_vector_store(chunks, context.vector_store_path)
                        
                        # Remove backup if successful
                        shutil.rmtree(backup_path)
                        optimized_count += 1
                    
                    except Exception as e:
                        # Restore backup if rebuild failed
                        shutil.rmtree(context.vector_store_path)
                        shutil.move(backup_path, context.vector_store_path)
                        print(f"Error optimizing vector store for context {context.id}: {e}")
            
            except Exception as e:
                print(f"Error processing context {context.id}: {e}")
                continue
        
        return f"Optimized {optimized_count} vector stores"
    
    except Exception as e:
        return f"Error during optimization: {str(e)}"
