"""
Celery tasks for context processing
"""

import os
import tempfile
import shutil
from datetime import datetime, timezone
from celery import current_app
from app import celery
from models import db, Context, Document
from services.repository_service import RepositoryService
from services.database_service import DatabaseService
from services.document_processor import DocumentProcessor
from services.vector_service import VectorService

@celery.task(bind=True)
def process_context_task(self, context_id: int):
    """Process a context in the background"""
    try:
        # Get context from database
        context = Context.query.get(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        # Update status
        context.status = 'processing'
        context.progress = 0
        context.error_message = None
        db.session.commit()
        
        # Process based on source type
        if context.source_type == 'repo':
            process_repository_context(context, self)
        elif context.source_type == 'database':
            process_database_context(context, self)
        elif context.source_type == 'files':
            process_files_context(context, self)
        else:
            raise ValueError(f"Unsupported source type: {context.source_type}")
        
        # Mark as ready
        context.status = 'ready'
        context.progress = 100
        db.session.commit()
        
        return f"Context {context_id} processed successfully"
    
    except Exception as e:
        # Mark as error
        context = Context.query.get(context_id)
        if context:
            context.status = 'error'
            context.error_message = str(e)
            db.session.commit()
        
        raise e

def process_repository_context(context: Context, task):
    """Process repository-based context"""
    config = context.get_config()
    repo_url = config.get('url')
    branch = config.get('branch', 'main')
    access_token = config.get('access_token')
    
    if not repo_url:
        raise ValueError("Repository URL is required")
    
    # Create temporary directory for cloning
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Update progress
        context.progress = 10
        db.session.commit()
        task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Cloning repository'})
        
        # Clone repository
        repo_service = RepositoryService()
        repo_dir = repo_service.clone_repository(repo_url, branch, access_token, temp_dir)
        
        # Update progress
        context.progress = 30
        db.session.commit()
        task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Processing files'})
        
        # Process files in repository
        document_processor = DocumentProcessor()
        all_chunks = []
        
        # Walk through repository files
        supported_extensions = set()
        for exts in document_processor.supported_extensions.values():
            supported_extensions.update(exts)
        
        file_count = 0
        processed_files = 0
        
        # Count total files first
        for root, dirs, files in os.walk(repo_dir):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            
            for file in files:
                if any(file.endswith(ext) for ext in supported_extensions):
                    file_count += 1
        
        # Process files
        for root, dirs, files in os.walk(repo_dir):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            
            for file in files:
                if any(file.endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_dir)
                    
                    try:
                        # Process file
                        chunks = document_processor.process_file(file_path, context.chunk_strategy)
                        
                        # Update chunk metadata with repository info
                        for chunk in chunks:
                            chunk['metadata']['repository_url'] = repo_url
                            chunk['metadata']['branch'] = branch
                            chunk['metadata']['relative_path'] = relative_path
                        
                        all_chunks.extend(chunks)
                        
                        # Create document record
                        document = Document(
                            context_id=context.id,
                            filename=file,
                            file_path=relative_path,
                            file_type=document_processor._get_file_type(os.path.splitext(file)[1].lower()),
                            file_size=os.path.getsize(file_path),
                            chunks_count=len(chunks),
                            processed_at=datetime.now(timezone.utc)
                        )
                        db.session.add(document)
                        
                        processed_files += 1
                        
                        # Update progress
                        progress = 30 + int((processed_files / file_count) * 40)
                        context.progress = progress
                        db.session.commit()
                        task.update_state(state='PROGRESS', meta={'progress': progress, 'status': f'Processed {processed_files}/{file_count} files'})
                    
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                        continue
        
        # Update progress
        context.progress = 70
        db.session.commit()
        task.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Creating vector store'})
        
        # Create vector store
        if all_chunks:
            vector_service = VectorService(context.embedding_model)
            vector_store_path = os.path.join('vector_store', f'context_{context.id}')
            
            vector_service.create_vector_store(all_chunks, vector_store_path)
            
            # Update context with vector store info
            context.vector_store_path = vector_store_path
            context.total_chunks = len(all_chunks)
            context.total_tokens = sum(len(chunk['content']) // 4 for chunk in all_chunks)
        
        # Update progress
        context.progress = 90
        db.session.commit()
        task.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalizing'})
    
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def process_database_context(context: Context, task):
    """Process database-based context"""
    config = context.get_config()
    db_type = config.get('type')
    connection_string = config.get('connection_string')
    tables = config.get('tables', [])
    
    if not db_type or not connection_string:
        raise ValueError("Database type and connection string are required")
    
    # Update progress
    context.progress = 10
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Connecting to database'})
    
    # Connect to database
    db_service = DatabaseService()
    
    # Test connection
    connection_test = db_service.test_connection(db_type, connection_string)
    if not connection_test.get('success'):
        raise ValueError(f"Database connection failed: {connection_test.get('error')}")
    
    # Update progress
    context.progress = 20
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Getting schema information'})
    
    # Get schema information
    schema_info = db_service.get_schema_info(db_type, connection_string)
    if not schema_info.get('success'):
        raise ValueError(f"Failed to get schema: {schema_info.get('error')}")
    
    # Update progress
    context.progress = 30
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Processing tables'})
    
    # Process tables
    document_processor = DocumentProcessor()
    all_chunks = []
    
    # If no specific tables specified, use all tables
    if not tables:
        if db_type == 'mongodb':
            tables = [col['name'] for col in schema_info.get('collections', [])]
        else:
            tables = [table['name'] for table in schema_info.get('tables', [])]
    
    total_tables = len(tables)
    processed_tables = 0
    
    for table_name in tables:
        try:
            # Extract table data
            df = db_service.extract_table_data(db_type, connection_string, table_name, limit=1000)
            
            # Process as dataframe
            chunks = document_processor._process_dataframe(df, f"database://{table_name}", db_type)
            
            # Update chunk metadata
            for chunk in chunks:
                chunk['metadata']['database_type'] = db_type
                chunk['metadata']['table_name'] = table_name
                chunk['metadata']['connection_info'] = {
                    'type': db_type,
                    'table': table_name
                }
            
            all_chunks.extend(chunks)
            
            # Create document record
            document = Document(
                context_id=context.id,
                filename=f"{table_name}.{db_type}",
                file_path=f"database://{table_name}",
                file_type='data',
                file_size=len(df) * len(df.columns) if not df.empty else 0,
                chunks_count=len(chunks),
                processed_at=datetime.now(timezone.utc)
            )
            db.session.add(document)
            
            processed_tables += 1
            
            # Update progress
            progress = 30 + int((processed_tables / total_tables) * 40)
            context.progress = progress
            db.session.commit()
            task.update_state(state='PROGRESS', meta={'progress': progress, 'status': f'Processed {processed_tables}/{total_tables} tables'})
        
        except Exception as e:
            print(f"Error processing table {table_name}: {e}")
            continue
    
    # Update progress
    context.progress = 70
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Creating vector store'})
    
    # Create vector store
    if all_chunks:
        vector_service = VectorService(context.embedding_model)
        vector_store_path = os.path.join('vector_store', f'context_{context.id}')
        
        vector_service.create_vector_store(all_chunks, vector_store_path)
        
        # Update context with vector store info
        context.vector_store_path = vector_store_path
        context.total_chunks = len(all_chunks)
        context.total_tokens = sum(len(chunk['content']) // 4 for chunk in all_chunks)
    
    # Update progress
    context.progress = 90
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalizing'})

def process_files_context(context: Context, task):
    """Process files-based context"""
    # Update progress
    context.progress = 10
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Processing uploaded files'})
    
    # Get uploaded documents
    documents = Document.query.filter_by(context_id=context.id).all()
    
    if not documents:
        raise ValueError("No files found for processing")
    
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
            
            all_chunks.extend(chunks)
            
            # Update document with processing info
            document.chunks_count = len(chunks)
            document.processed_at = datetime.utcnow()
            
            processed_files += 1
            
            # Update progress
            progress = 10 + int((processed_files / total_files) * 60)
            context.progress = progress
            db.session.commit()
            task.update_state(state='PROGRESS', meta={'progress': progress, 'status': f'Processed {processed_files}/{total_files} files'})
        
        except Exception as e:
            print(f"Error processing file {document.filename}: {e}")
            continue
    
    # Update progress
    context.progress = 70
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Creating vector store'})
    
    # Create vector store
    if all_chunks:
        vector_service = VectorService(context.embedding_model)
        vector_store_path = os.path.join('vector_store', f'context_{context.id}')
        
        vector_service.create_vector_store(all_chunks, vector_store_path)
        
        # Update context with vector store info
        context.vector_store_path = vector_store_path
        context.total_chunks = len(all_chunks)
        context.total_tokens = sum(len(chunk['content']) // 4 for chunk in all_chunks)
    
    # Update progress
    context.progress = 90
    db.session.commit()
    task.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalizing'})
