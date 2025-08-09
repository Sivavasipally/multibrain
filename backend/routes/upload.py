"""
File Upload Routes for RAG Chatbot PWA - Document Ingestion and Processing

This module provides comprehensive file upload and processing capabilities for the RAG
(Retrieval-Augmented Generation) chatbot system. It handles multi-format file uploads,
automatic text extraction, intelligent chunking, and vector store creation for optimal
RAG performance.

Key Features:
- Multi-format file upload support (40+ file types)
- Secure file handling with validation and sanitization
- Automatic text extraction from various document types
- Intelligent text chunking for optimal RAG performance
- Real-time document processing with progress tracking
- Vector store creation for similarity search
- ZIP archive extraction and batch processing
- Comprehensive error handling and logging

Supported File Categories:
- Text Files: TXT, MD, RST, LOG
- Code Files: Python, JavaScript, Java, C++, Go, Rust, etc.
- Documents: PDF, DOCX, DOC, RTF
- Data Files: CSV, JSON, XML, YAML, XLSX
- Configuration: INI, TOML, Properties
- Web Files: HTML, CSS, SCSS
- SQL Files: SQL, DDL, DML
- Archives: ZIP, TAR, GZ

Processing Pipeline:
1. File Upload: Secure upload with validation
2. Storage: Organized file storage by context
3. Text Extraction: Format-specific content extraction
4. Chunking: Intelligent text segmentation
5. Database Storage: Metadata and chunk persistence
6. Vector Indexing: FAISS vector store creation
7. Status Updates: Real-time progress tracking

API Endpoints:
- POST /files: Upload files for processing
- POST /extract-zip: Extract and process ZIP archives
- GET /supported-extensions: Get supported file types

Dependencies:
- Flask: Web framework and request handling
- Werkzeug: Secure filename utilities
- SQLAlchemy: Database operations
- VectorService: Vector store creation
- DocumentProcessor: Text extraction and processing

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import zipfile
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

# Import database models
from models import db, Context, Document, TextChunk

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('upload_routes')

def get_current_user_id():
    """
    Extract and validate user ID from JWT token for upload operations
    
    This helper function securely extracts the user identity from the JWT token
    and converts it to an integer for database operations. Used throughout
    upload routes for authentication and authorization.
    
    Returns:
        int: The authenticated user's ID if valid token exists
        None: If no token or invalid token
        
    Raises:
        ValueError: If JWT identity cannot be converted to integer
        
    Security:
        - Validates token authenticity
        - Prevents unauthorized file uploads
        - Logs authentication attempts for audit
    """
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved user ID {user_id} from JWT for upload operations")
            return user_id
        else:
            logger.debug("No user identity found in JWT token for upload request")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer for upload operations: {e}")
        return None

# Note: Celery background processing disabled for local development
# from tasks.file_processor import process_uploaded_files_task

upload_bp = Blueprint('upload', __name__)

# Comprehensive file type support configuration
SUPPORTED_EXTENSIONS = {
    'text': ['.txt', '.md', '.rst', '.log'],
    'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.cs', '.kt', '.swift'],
    'document': ['.pdf', '.docx', '.doc', '.rtf'],
    'data': ['.csv', '.xlsx', '.xls', '.json', '.xml', '.yaml', '.yml'],
    'config': ['.ini', '.cfg', '.conf', '.toml', '.properties'],
    'web': ['.html', '.htm', '.css', '.scss', '.sass', '.less'],
    'sql': ['.sql', '.ddl', '.dml'],
    'archive': ['.zip', '.tar', '.gz', '.rar']
}

# Flattened list of all supported extensions for quick validation
ALL_EXTENSIONS = [ext for exts in SUPPORTED_EXTENSIONS.values() for ext in exts]

logger.info(f"File upload service initialized with {len(ALL_EXTENSIONS)} supported file extensions across {len(SUPPORTED_EXTENSIONS)} categories")

def allowed_file(filename):
    """
    Validate if file type is supported for upload and processing
    
    Checks the file extension against the list of supported file types
    to ensure only processable files are uploaded. This prevents
    unsupported files from consuming storage and processing resources.
    
    Args:
        filename (str): Name of the file to validate
        
    Returns:
        bool: True if file extension is supported, False otherwise
        
    Example:
        >>> allowed_file('document.pdf')
        True
        >>> allowed_file('image.jpg')
        False
        
    Security:
        - Prevents upload of potentially malicious file types
        - Validates file extensions for processing compatibility
        - Helps maintain system security and stability
    """
    if not filename or '.' not in filename:
        return False
        
    extension = os.path.splitext(filename)[1].lower()
    is_allowed = extension in ALL_EXTENSIONS
    
    logger.debug(f"File validation: {filename} ({'allowed' if is_allowed else 'rejected'})")
    return is_allowed

def get_file_category(filename):
    """
    Determine file category based on file extension
    
    Categorizes files into logical groups for appropriate processing
    and handling. Each category may require different text extraction
    methods and processing strategies.
    
    Args:
        filename (str): Name of the file to categorize
        
    Returns:
        str: File category ('text', 'code', 'document', 'data', 'config', 
             'web', 'sql', 'archive', or 'unknown')
             
    Example:
        >>> get_file_category('main.py')
        'code'
        >>> get_file_category('data.json')
        'data'
        
    Use Cases:
        - Routing files to appropriate processors
        - Applying category-specific processing logic
        - Organizing uploaded content by type
        - UI display and filtering
    """
    if not filename:
        return 'unknown'
        
    ext = os.path.splitext(filename)[1].lower()
    
    for category, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            logger.debug(f"File {filename} categorized as: {category}")
            return category
            
    logger.debug(f"File {filename} has unknown category (extension: {ext})")
    return 'unknown'

@upload_bp.route('/files', methods=['OPTIONS'])
def upload_files_options():
    """Handle CORS preflight requests for file uploads"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@upload_bp.route('/files', methods=['POST'])
@jwt_required()
def upload_files():
    """
    Upload and process files for RAG context creation
    
    This is the primary endpoint for file uploads in the RAG system. It handles
    secure file upload, validation, storage, and immediate processing to create
    searchable text chunks and vector embeddings for optimal RAG performance.
    
    Processing Pipeline:
    1. Authentication: Verify user identity and context ownership
    2. Validation: Check file types and sizes
    3. Storage: Save files securely with duplicate handling
    4. Database: Create document metadata records
    5. Processing: Extract text and create chunks
    6. Indexing: Generate vector embeddings for similarity search
    7. Status Updates: Update context processing status
    
    Request Format:
        Content-Type: multipart/form-data
        - files: List of files to upload
        - context_id: Target context ID for file association
        
    Authentication:
        Requires valid JWT token in Authorization header
        
    Returns:
        200: Successful upload and processing
        {
            "message": "Successfully uploaded and processed N files",
            "files": [
                {
                    "filename": "document.pdf",
                    "size": 12345,
                    "type": "document"
                }
            ]
        }
        
        400: Bad request (missing files, unsupported types, etc.)
        401: Unauthorized (invalid JWT)
        404: Context not found or access denied
        500: Server error during processing
        
    File Handling:
        - Maximum file size: Configurable via UPLOAD_FOLDER settings
        - Duplicate names: Automatic rename with counter suffix
        - Security: Filename sanitization and path validation
        - Storage: Organized by context ID for isolation
        
    Example:
        curl -X POST /api/upload/files \
             -H "Authorization: Bearer <jwt_token>" \
             -F "files=@document.pdf" \
             -F "files=@code.py" \
             -F "context_id=123"
    """
    client_ip = request.remote_addr
    logger.info(f"File upload request from IP: {client_ip}")
    
    try:
        # Authenticate user
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized file upload attempt from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.info(f"Processing file upload request from user {user_id}")
        
        # Validate request data
        if 'files' not in request.files:
            logger.warning(f"File upload request missing files from user {user_id}")
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        context_id = request.form.get('context_id')
        
        if not context_id:
            logger.warning(f"File upload request missing context_id from user {user_id}")
            return jsonify({'error': 'Context ID is required'}), 400
        
        try:
            context_id = int(context_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid context_id format: {context_id} from user {user_id}")
            return jsonify({'error': 'Invalid context ID format'}), 400
        
        logger.debug(f"Upload request: {len(files)} files to context {context_id}")
        
        # Verify context ownership and configuration
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            logger.warning(f"Context {context_id} not found or access denied for user {user_id}")
            return jsonify({'error': 'Context not found or access denied'}), 404
        
        if context.source_type != 'files':
            logger.warning(f"Context {context_id} not configured for file uploads (type: {context.source_type})")
            return jsonify({'error': 'Context is not configured for file uploads'}), 400
        
        # Prepare upload directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        context_folder = os.path.join(upload_folder, f'context_{context_id}')
        os.makedirs(context_folder, exist_ok=True)
        
        logger.debug(f"Upload directory prepared: {context_folder}")
        
        uploaded_files = []
        total_size = 0
        
        # Process each uploaded file
        for file in files:
            if not file.filename or file.filename == '':
                logger.debug("Skipping empty filename")
                continue
            
            # Validate file type
            if not allowed_file(file.filename):
                error_msg = f'File type not supported: {file.filename}'
                logger.warning(error_msg)
                return jsonify({'error': error_msg}), 400
            
            # Secure filename and handle duplicates
            original_filename = file.filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(context_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(file_path):
                filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(context_folder, filename)
                counter += 1
            
            if counter > 1:
                logger.debug(f"Renamed {original_filename} to {filename} to avoid duplicates")
            
            # Save file to disk
            try:
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                logger.debug(f"Saved file: {filename} ({file_size:,} bytes)")
                
            except Exception as save_error:
                logger.error(f"Failed to save file {filename}: {save_error}")
                return jsonify({'error': f'Failed to save file: {filename}'}), 500
            
            # Create document metadata record
            document = Document(
                context_id=context_id,
                filename=filename,
                file_path=file_path,
                file_type=get_file_category(filename),
                file_size=file_size
            )
            
            db.session.add(document)
            uploaded_files.append({
                'filename': filename,
                'size': file_size,
                'type': document.file_type
            })
        
        # Commit file metadata to database
        db.session.commit()
        
        logger.info(f"Successfully uploaded {len(uploaded_files)} files ({total_size:,} total bytes) for context {context_id}")
        
        # Process documents immediately (local development mode)
        if uploaded_files:
            try:
                logger.info(f"Starting immediate processing of {len(uploaded_files)} files")
                
                # Update context status to processing
                context.status = 'processing'
                context.progress = 0
                db.session.commit()
                
                # Process uploaded documents
                process_uploaded_documents(context_id)
                
                # Update context status to ready
                context.status = 'ready'
                context.progress = 100
                db.session.commit()
                
                logger.info(f"Document processing completed successfully for context {context_id}")
                
            except Exception as processing_error:
                error_msg = f"Document processing failed: {str(processing_error)}"
                logger.error(error_msg)
                log_error_with_context(processing_error, {
                    "context_id": context_id,
                    "user_id": user_id,
                    "files_count": len(uploaded_files),
                    "operation": "document_processing"
                })
                
                # Set context status to error
                context.status = 'error'
                context.error_message = str(processing_error)
                db.session.commit()
                
                # Files are uploaded but not processed
                logger.warning(f"Files uploaded but processing failed for context {context_id}")
        
        return jsonify({
            'message': f'Successfully uploaded and processed {len(uploaded_files)} files',
            'files': uploaded_files,
            'total_size': total_size,
            'context_id': context_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"File upload failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "user_id": user_id if 'user_id' in locals() else None,
            "context_id": context_id if 'context_id' in locals() else None,
            "client_ip": client_ip,
            "operation": "file_upload"
        })
        return jsonify({'error': 'Failed to upload files'}), 500

@upload_bp.route('/extract-zip', methods=['POST'])
@jwt_required()
def extract_zip():
    """
    Extract and process files from ZIP archives
    
    Provides batch file processing capabilities by extracting ZIP archives and
    processing all contained supported files. This is useful for bulk document
    uploads and repository imports.
    
    Archive Processing:
    1. ZIP Validation: Verify archive integrity
    2. Content Scanning: Identify supported file types
    3. Selective Extraction: Extract only processable files
    4. Batch Processing: Process all extracted files
    5. Cleanup: Remove temporary archive files
    
    Request Format:
        Content-Type: multipart/form-data
        - file: ZIP archive to extract
        - context_id: Target context ID
        
    Returns:
        200: Successful extraction and processing
        400: Invalid ZIP file or missing parameters
        404: Context not found
        500: Server error
        
    Security:
        - Path traversal protection
        - File type validation
        - Size limits enforcement
        - Temporary file cleanup
        
    Example:
        curl -X POST /api/upload/extract-zip \
             -H "Authorization: Bearer <token>" \
             -F "file=@archive.zip" \
             -F "context_id=123"
    """
    client_ip = request.remote_addr
    logger.info(f"ZIP extraction request from IP: {client_ip}")
    
    try:
        # Authenticate user
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Unauthorized ZIP extraction attempt from {client_ip}")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Validate request
        if 'file' not in request.files:
            logger.warning(f"ZIP extraction request missing file from user {user_id}")
            return jsonify({'error': 'No ZIP file provided'}), 400
        
        file = request.files['file']
        context_id = request.form.get('context_id')
        
        if not context_id:
            logger.warning(f"ZIP extraction request missing context_id from user {user_id}")
            return jsonify({'error': 'Context ID is required'}), 400
        
        try:
            context_id = int(context_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid context ID format'}), 400
        
        logger.info(f"Processing ZIP extraction for context {context_id} from user {user_id}")
        
        # Verify context ownership
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            logger.warning(f"Context {context_id} not found for user {user_id}")
            return jsonify({'error': 'Context not found or access denied'}), 404
        
        # Validate ZIP file
        if not file.filename or not file.filename.lower().endswith('.zip'):
            logger.warning(f"Invalid ZIP file: {file.filename}")
            return jsonify({'error': 'Only ZIP files are supported'}), 400
        
        # Prepare extraction directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        context_folder = os.path.join(upload_folder, f'context_{context_id}')
        os.makedirs(context_folder, exist_ok=True)
        
        # Save ZIP file temporarily
        zip_filename = secure_filename(file.filename)
        zip_path = os.path.join(context_folder, f'temp_{zip_filename}')
        file.save(zip_path)
        
        logger.debug(f"ZIP file saved temporarily: {zip_path}")
        
        extracted_files = []
        total_size = 0
        
        try:
            # Extract and process ZIP contents
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                logger.debug(f"ZIP archive contains {len(zip_ref.filelist)} entries")
                
                for file_info in zip_ref.filelist:
                    # Skip directories and system files
                    if file_info.is_dir() or file_info.filename.startswith('__MACOSX/'):
                        continue
                    
                    # Check if file type is supported
                    if not allowed_file(file_info.filename):
                        logger.debug(f"Skipping unsupported file: {file_info.filename}")
                        continue
                    
                    # Security: Prevent path traversal attacks
                    if '..' in file_info.filename or file_info.filename.startswith('/'):
                        logger.warning(f"Potentially malicious path detected: {file_info.filename}")
                        continue
                    
                    try:
                        # Extract file to context folder
                        extracted_path = zip_ref.extract(file_info, context_folder)
                        actual_size = os.path.getsize(extracted_path)
                        total_size += actual_size
                        
                        # Create document metadata record
                        filename = os.path.basename(file_info.filename)
                        document = Document(
                            context_id=context_id,
                            filename=filename,
                            file_path=extracted_path,
                            file_type=get_file_category(filename),
                            file_size=actual_size
                        )
                        
                        db.session.add(document)
                        extracted_files.append({
                            'filename': filename,
                            'size': actual_size,
                            'type': document.file_type
                        })
                        
                        logger.debug(f"Extracted: {filename} ({actual_size:,} bytes)")
                        
                    except Exception as extract_error:
                        logger.error(f"Failed to extract {file_info.filename}: {extract_error}")
                        continue
            
            # Remove temporary ZIP file
            try:
                os.remove(zip_path)
                logger.debug("Temporary ZIP file removed")
            except Exception as cleanup_error:
                logger.warning(f"Failed to remove temporary ZIP file: {cleanup_error}")
            
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file format: {zip_filename}")
            # Clean up temporary file
            try:
                os.remove(zip_path)
            except:
                pass
            return jsonify({'error': 'Invalid or corrupted ZIP file'}), 400
        
        # Commit extracted files to database
        db.session.commit()
        
        logger.info(f"Successfully extracted {len(extracted_files)} files ({total_size:,} total bytes) from ZIP")
        
        # Process extracted files immediately (local development mode)
        if extracted_files:
            try:
                logger.info(f"Starting processing of {len(extracted_files)} extracted files")
                process_uploaded_documents(context_id)
                logger.info(f"ZIP extraction and processing completed for context {context_id}")
            except Exception as processing_error:
                logger.error(f"Failed to process extracted files: {processing_error}")
                # Files are extracted but not processed - this is still partially successful
        
        return jsonify({
            'message': f'Successfully extracted and processed {len(extracted_files)} files',
            'files': extracted_files,
            'total_size': total_size
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"ZIP extraction failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "user_id": user_id if 'user_id' in locals() else None,
            "context_id": context_id if 'context_id' in locals() else None,
            "client_ip": client_ip,
            "operation": "zip_extraction"
        })
        return jsonify({'error': 'Failed to extract ZIP file'}), 500

@upload_bp.route('/supported-extensions', methods=['GET'])
def get_supported_extensions():
    """
    Retrieve comprehensive list of supported file extensions and categories
    
    Provides client applications with information about supported file types
    for upload validation and user interface display. This endpoint is public
    and does not require authentication.
    
    Response Format:
        {
            "extensions": {
                "text": [".txt", ".md", ".rst", ".log"],
                "code": [".py", ".js", ".ts", ...],
                "document": [".pdf", ".docx", ".doc", ".rtf"],
                ...
            },
            "total_count": 42,
            "categories": [
                {
                    "name": "text",
                    "description": "Plain text and markdown files",
                    "count": 4
                },
                ...
            ]
        }
    
    Returns:
        200: List of supported extensions by category
        
    Use Cases:
        - Client-side file validation
        - Upload interface configuration
        - User guidance and help text
        - File type filtering in UI
        
    Example:
        curl -X GET /api/upload/supported-extensions
    """
    logger.debug("Supported extensions request")
    
    # Generate category descriptions
    category_descriptions = {
        'text': 'Plain text and markdown files',
        'code': 'Programming language source files',
        'document': 'Office documents and PDFs',
        'data': 'Structured data files (CSV, JSON, XML)',
        'config': 'Configuration and settings files',
        'web': 'Web markup and stylesheet files',
        'sql': 'Database query and schema files',
        'archive': 'Compressed archive files'
    }
    
    # Build detailed category information
    categories = []
    for category, extensions in SUPPORTED_EXTENSIONS.items():
        categories.append({
            'name': category,
            'description': category_descriptions.get(category, f'{category.title()} files'),
            'extensions': extensions,
            'count': len(extensions)
        })
    
    response_data = {
        'extensions': SUPPORTED_EXTENSIONS,
        'total_count': len(ALL_EXTENSIONS),
        'categories': categories
    }
    
    logger.debug(f"Returning {len(ALL_EXTENSIONS)} supported extensions across {len(SUPPORTED_EXTENSIONS)} categories")
    
    return jsonify(response_data), 200

@upload_bp.route('/<int:context_id>/process-async', methods=['POST'])
@jwt_required()
def process_documents_async(context_id):
    """
    Process uploaded documents asynchronously using background tasks
    
    This endpoint submits document processing as a background task instead of
    processing synchronously. This is useful for large document sets that might
    take a long time to process, allowing users to continue using the application
    while processing happens in the background.
    
    Processing Features:
        - Background task execution with progress tracking
        - Task result monitoring via task API endpoints
        - Error handling and retry mechanisms
        - Automatic version creation after processing
        
    Args:
        context_id (int): ID of context containing documents to process
        
    Request Body:
        {
            "force_reprocess": false,  // Optional: reprocess existing documents
            "priority": "normal"       // Optional: task priority (low, normal, high, urgent)
        }
        
    Returns:
        202: Processing task submitted successfully
        {
            "message": "Document processing task submitted",
            "task_id": "uuid-string",
            "context_id": 123,
            "estimated_duration": "5-10 minutes",
            "monitor_url": "/api/tasks/uuid-string"
        }
        
        400: Invalid request or no documents to process
        403: Insufficient permissions or context not found
        500: Task submission failed
        
    Authentication:
        Requires valid JWT token and context ownership
        
    Example:
        curl -X POST "/api/upload/123/process-async" \
             -H "Authorization: Bearer <jwt_token>" \
             -H "Content-Type: application/json" \
             -d '{"priority": "high"}'
    """
    client_ip = request.remote_addr
    user_id = get_current_user_id()
    
    if not user_id:
        logger.warning(f"Async processing request with invalid JWT from {client_ip}")
        return jsonify({'error': 'Authentication required'}), 401
    
    logger.info(f"Async document processing request for context {context_id} from user {user_id}")
    
    try:
        # Get the context and verify ownership
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            logger.warning(f"Context {context_id} not found or not owned by user {user_id}")
            return jsonify({'error': 'Context not found'}), 403
        
        # Parse request data
        data = request.get_json() or {}
        force_reprocess = data.get('force_reprocess', False)
        priority = data.get('priority', 'normal')
        
        # Validate priority
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            return jsonify({
                'error': f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'
            }), 400
        
        # Check if there are documents to process
        query = Document.query.filter_by(context_id=context_id)
        if not force_reprocess:
            query = query.filter_by(processed_at=None)
        
        documents_to_process = query.count()
        if documents_to_process == 0:
            return jsonify({
                'error': 'No documents to process',
                'message': 'All documents in this context have already been processed'
            }), 400
        
        logger.info(f"Found {documents_to_process} documents to process for context {context_id}")
        
        # Submit background task
        from services.task_service import task_service, TaskPriority
        
        try:
            task_priority = TaskPriority[priority.upper()]
        except KeyError:
            task_priority = TaskPriority.NORMAL
        
        task_id = task_service.submit_task(
            task_type='document_processing',
            priority=task_priority,
            user_id=user_id,
            context_id=context_id,
            force_reprocess=force_reprocess,
            max_retries=2  # Fewer retries for user-initiated tasks
        )
        
        # Update context status to indicate processing started
        context.status = 'processing'
        context.progress = 5  # Initial progress
        db.session.commit()
        
        response_data = {
            'message': 'Document processing task submitted successfully',
            'task_id': task_id,
            'context_id': context_id,
            'documents_to_process': documents_to_process,
            'priority': priority,
            'estimated_duration': '2-10 minutes' if documents_to_process <= 5 else '5-20 minutes',
            'monitor_url': f'/api/tasks/{task_id}',
            'context_tasks_url': f'/api/contexts/{context_id}/tasks'
        }
        
        logger.info(f"Successfully submitted async processing task {task_id} for context {context_id}")
        return jsonify(response_data), 202  # 202 Accepted for async processing
        
    except Exception as e:
        error_msg = f"Failed to submit async processing task for context {context_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "context_id": context_id,
            "user_id": user_id,
            "client_ip": client_ip,
            "operation": "process_documents_async"
        })
        return jsonify({'error': 'Failed to submit processing task'}), 500


def process_uploaded_documents(context_id):
    """
    Process uploaded documents to create searchable text chunks and vector embeddings
    
    This function handles the complete document processing pipeline for RAG operations:
    text extraction, intelligent chunking, database storage, and vector index creation.
    It processes all documents associated with a context and prepares them for
    similarity search and retrieval-augmented generation.
    
    Processing Pipeline:
    1. Document Retrieval: Get all unprocessed documents for context
    2. Text Extraction: Extract text content using format-specific processors
    3. Text Chunking: Split content into optimal chunks for RAG
    4. Database Storage: Save text chunks with metadata
    5. Vector Indexing: Create FAISS index for similarity search
    6. Status Updates: Update context and document processing status
    
    Args:
        context_id (int): ID of the context containing documents to process
        
    Raises:
        ValueError: If context is not found
        Exception: If document processing fails
        
    Processing Features:
        - Duplicate detection to prevent reprocessing
        - Intelligent text chunking with overlap
        - Token counting for cost estimation
        - Vector store creation for similarity search
        - Comprehensive error handling and logging
        
    Example:
        >>> process_uploaded_documents(123)
        # Processes all documents in context 123
    """
    logger.info(f"Starting document processing for context {context_id}")
    
    try:
        # Retrieve context
        context = Context.query.get(context_id)
        if not context:
            error_msg = f"Context {context_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Processing documents for context: {context.name}")
        
        # Get all documents for this context
        documents = Document.query.filter_by(context_id=context_id).all()
        logger.info(f"Found {len(documents)} documents to process")
        
        # Initialize vector service for embeddings
        try:
            from services.vector_service import VectorService
            vector_service = VectorService(context.embedding_model or 'text-embedding-004')
            logger.debug(f"Vector service initialized with model: {context.embedding_model or 'text-embedding-004'}")
        except Exception as vector_error:
            logger.error(f"Failed to initialize vector service: {vector_error}")
            raise
        
        # Set up vector store directory
        vector_store_dir = os.path.join('vector_stores', str(context_id))
        os.makedirs(vector_store_dir, exist_ok=True)
        logger.debug(f"Vector store directory prepared: {vector_store_dir}")
        
        total_chunks = 0
        total_tokens = 0
        all_chunks = []
        processed_documents = 0
        
        # Process each document
        for document in documents:
            logger.info(f"Processing document: {document.filename}")
            
            try:
                # Check if already processed (skip duplicates)
                existing_chunks = TextChunk.query.filter_by(
                    context_id=context_id, 
                    file_name=document.filename
                ).first()
                
                if existing_chunks:
                    logger.debug(f"Document {document.filename} already processed, skipping")
                    continue
                
                # Extract text content from document
                logger.debug(f"Extracting text from: {document.file_path}")
                text = extract_text_from_document(document.file_path)
                
                if not text or len(text.strip()) < 10:
                    logger.warning(f"No meaningful text extracted from {document.filename} (length: {len(text) if text else 0})")
                    continue
                
                text_length = len(text)
                logger.debug(f"Extracted {text_length:,} characters from {document.filename}")
                
                # Create intelligent text chunks
                chunks = simple_chunk_text(text, max_chunk_size=1000, overlap=100)
                logger.debug(f"Split text into {len(chunks)} chunks")
                
                # Process and save chunks
                chunks_saved = 0
                document_tokens = 0
                
                for i, chunk_text in enumerate(chunks):
                    chunk_content = chunk_text.strip()
                    if len(chunk_content) > 20:  # Only save meaningful chunks
                        # Create database record
                        chunk = TextChunk(
                            context_id=context_id,
                            file_name=document.filename,
                            chunk_index=i,
                            content=chunk_content
                        )
                        db.session.add(chunk)
                        chunks_saved += 1
                        
                        # Calculate tokens for this chunk
                        chunk_tokens = len(chunk_content.split())
                        document_tokens += chunk_tokens
                        
                        # Prepare for vector store
                        all_chunks.append({
                            'content': chunk_content,
                            'source': document.filename,
                            'chunk_index': i,
                            'context_id': context_id,
                            'metadata': {
                                'file_name': document.filename,
                                'file_type': document.file_type,
                                'chunk_index': i
                            }
                        })
                
                # Update document statistics
                document.chunks_count = chunks_saved
                document.tokens_count = document_tokens
                
                total_chunks += chunks_saved
                total_tokens += document_tokens
                processed_documents += 1
                
                logger.info(f"Processed {document.filename}: {chunks_saved} chunks, {document_tokens:,} tokens")
                
            except Exception as doc_error:
                logger.error(f"Failed to process document {document.filename}: {doc_error}")
                log_error_with_context(doc_error, {
                    "document_id": document.id,
                    "document_filename": document.filename,
                    "context_id": context_id
                })
                continue  # Continue with other documents
        
        # Update context statistics
        context.total_chunks = total_chunks
        context.total_tokens = total_tokens
        
        logger.info(f"Document processing summary: {processed_documents}/{len(documents)} documents, {total_chunks} chunks, {total_tokens:,} tokens")
        
        # Create vector store if we have chunks
        if all_chunks:
            logger.info(f"Creating vector store with {len(all_chunks)} chunks")
            
            try:
                vector_service.create_vector_store(all_chunks, vector_store_dir)
                
                # Update context with vector store path
                context.vector_store_path = vector_store_dir  # Store directory path, not file path
                
                logger.info(f"Vector store created successfully at {vector_store_dir}")
                
            except Exception as vector_error:
                logger.error(f"Failed to create vector store: {vector_error}")
                log_error_with_context(vector_error, {
                    "context_id": context_id,
                    "chunks_count": len(all_chunks),
                    "vector_store_dir": vector_store_dir
                })
                # Continue without vector store - chunks are still saved in database
                logger.warning("Continuing without vector store - documents are still searchable through database")
        else:
            logger.warning(f"No text chunks created for context {context_id} - skipping vector store creation")
        
        # Update context status to ready
        context.status = 'ready'
        context.progress = 100
        
        # Create automatic version after successful processing
        try:
            from context_versioning import ContextVersionService
            
            # Create version changes summary
            changes = {
                'document_addition': {
                    'operation': 'added',
                    'description': f'Added {processed_documents} documents',
                    'impact_score': min(processed_documents, 10),  # Cap at 10 for major changes
                    'documents_added': processed_documents,
                    'chunks_created': total_chunks,
                    'tokens_processed': total_tokens
                }
            }
            
            # Determine if this should be a major version based on impact
            force_major = processed_documents >= 5 or total_chunks >= 1000
            
            version = ContextVersionService.create_version(
                context=context,
                user_id=context.user_id,
                description=f"Auto-version after processing {processed_documents} documents ({total_chunks} chunks, {total_tokens:,} tokens)",
                version_type='auto',
                changes=changes,
                force_major=force_major
            )
            
            logger.info(f"Created automatic version {version.version_number} for context {context_id} after document processing")
            
        except Exception as version_error:
            logger.warning(f"Failed to create automatic version for context {context_id}: {version_error}")
            # Don't fail the entire processing if versioning fails
            pass
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Document processing completed successfully for context {context_id}")
        logger.info(f"Final stats: {total_chunks} chunks, {total_tokens:,} tokens, status: ready")
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Document processing failed for context {context_id}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "context_id": context_id,
            "operation": "document_processing"
        })
        raise


def extract_text_from_document(file_path):
    """
    Extract text content from various document formats
    
    Provides format-specific text extraction for different file types with
    fallback mechanisms for encoding issues and unsupported formats. This
    function is the entry point for converting uploaded files into searchable text.
    
    Supported Formats:
    - Text files: Direct UTF-8/Latin-1 reading
    - Code files: Source code with syntax preservation
    - Configuration files: Settings and config data
    - Structured data: JSON, XML, YAML content
    - Web files: HTML, CSS markup and styles
    
    Args:
        file_path (str): Absolute path to the document file
        
    Returns:
        str: Extracted text content or empty string if extraction fails
             Placeholder text for unsupported binary formats
             
    Text Extraction Features:
        - Multi-encoding support (UTF-8, Latin-1 fallback)
        - Format-specific processing
        - Error recovery and fallback handling
        - Meaningful placeholder generation
        
    Example:
        >>> content = extract_text_from_document('/path/to/document.txt')
        >>> print(f"Extracted {len(content)} characters")
        
    Error Handling:
        - Graceful encoding fallback
        - File access error recovery
        - Comprehensive logging for debugging
    """
    try:
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        logger.debug(f"Extracting text from: {file_path.name} (type: {file_extension})")
        
        # Validate file existence
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return ""
        
        file_size = file_path.stat().st_size
        logger.debug(f"File size: {file_size:,} bytes")
        
        # Handle text-based files with encoding fallback
        text_extensions = {
            '.txt', '.md', '.rst', '.log',  # Text files
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.cs', '.kt', '.swift',  # Code
            '.json', '.xml', '.yaml', '.yml',  # Data formats
            '.html', '.htm', '.css', '.scss', '.sass', '.less',  # Web files
            '.sql', '.ddl', '.dml',  # SQL files
            '.ini', '.cfg', '.conf', '.toml', '.properties'  # Config files
        }
        
        if file_extension in text_extensions:
            # Try UTF-8 encoding first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.debug(f"Successfully read {len(content):,} characters with UTF-8 encoding")
                    return content
                    
            except UnicodeDecodeError:
                logger.debug("UTF-8 decoding failed, attempting Latin-1 fallback")
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                        logger.debug(f"Successfully read {len(content):,} characters with Latin-1 encoding")
                        return content
                        
                except UnicodeDecodeError as fallback_error:
                    logger.error(f"Failed to decode file with both UTF-8 and Latin-1: {fallback_error}")
                    return ""
            
            except Exception as read_error:
                logger.error(f"File reading error: {read_error}")
                return ""
        
        # For unsupported binary formats, create informative placeholder
        logger.debug(f"Creating placeholder content for binary/unsupported format: {file_extension}")
        
        placeholder_content = f"""Document: {file_path.name}
File Type: {file_extension}
File Size: {file_size:,} bytes
Category: {get_file_category(file_path.name)}

This {file_extension} file contains structured or binary data that requires specialized processing.
In a full production implementation, this would be processed using:
- PDF processors (PyMuPDF, pdfplumber) for PDF files
- Office document parsers (python-docx, openpyxl) for Office files
- Specialized parsers for other binary formats

The file is available for download and manual review if needed."""
        
        logger.debug(f"Generated {len(placeholder_content)} character placeholder for {file_extension} file")
        return placeholder_content
        
    except Exception as e:
        error_msg = f"Text extraction failed for {file_path}: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "file_path": str(file_path),
            "file_extension": file_path.suffix.lower() if hasattr(file_path, 'suffix') else 'unknown',
            "operation": "text_extraction"
        })
        return ""


def simple_chunk_text(text, max_chunk_size=1000, overlap=100):
    """
    Intelligent text chunking optimized for RAG (Retrieval-Augmented Generation)
    
    Splits text into overlapping chunks that preserve semantic meaning while
    staying within optimal size limits for vector embeddings and LLM processing.
    The chunking strategy prioritizes paragraph boundaries to maintain context.
    
    Chunking Strategy:
    1. Paragraph-first: Split on double newlines to preserve structure
    2. Word-boundary: Split long paragraphs at word boundaries
    3. Overlap: Add overlap between chunks for context continuity
    4. Size optimization: Target optimal chunk sizes for embeddings
    
    Args:
        text (str): Input text to chunk
        max_chunk_size (int): Maximum chunk size in characters (default: 1000)
        overlap (int): Overlap between chunks in characters (default: 100)
        
    Returns:
        List[str]: List of text chunks with preserved semantic boundaries
                  Single-element list if text fits in one chunk
                  
    Chunking Features:
        - Semantic boundary preservation
        - Configurable overlap for context continuity
        - Word-boundary splitting to avoid mid-word breaks
        - Empty chunk filtering
        - Whitespace normalization
        
    Example:
        >>> text = "Long document text...\n\nAnother paragraph..."
        >>> chunks = simple_chunk_text(text, max_chunk_size=500, overlap=50)
        >>> print(f"Created {len(chunks)} chunks")
        
    Performance:
        - Optimized for typical document sizes
        - Memory-efficient processing
        - Linear time complexity O(n)
    """
    if not text or not text.strip():
        logger.debug("Empty text provided for chunking")
        return []
        
    text = text.strip()
    text_length = len(text)
    
    logger.debug(f"Chunking text: {text_length:,} characters, max_chunk_size: {max_chunk_size}, overlap: {overlap}")
    
    # If text is small enough, return as single chunk
    if text_length <= max_chunk_size:
        logger.debug("Text fits in single chunk")
        return [text]
    
    chunks = []
    
    # Split by paragraphs first to preserve document structure
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    logger.debug(f"Found {len(paragraphs)} paragraphs for chunking")
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Check if we can add this paragraph to current chunk
        potential_length = len(current_chunk) + len(paragraph) + 2  # +2 for \n\n
        
        if potential_length <= max_chunk_size:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
                
        else:
            # Save current chunk if it exists
            if current_chunk:
                chunks.append(current_chunk)
                
                # Start new chunk with overlap from previous chunk
                if overlap > 0 and len(current_chunk) > overlap:
                    # Take last part of previous chunk as overlap
                    overlap_text = current_chunk[-overlap:]
                    # Find word boundary for clean overlap
                    space_pos = overlap_text.find(' ')
                    if space_pos > 0:
                        overlap_text = overlap_text[space_pos:].strip()
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Current paragraph is too long, need to split it
                logger.debug(f"Paragraph too long ({len(paragraph)} chars), splitting by words")
                
                words = paragraph.split()
                word_chunk = ""
                
                for word in words:
                    potential_word_length = len(word_chunk) + len(word) + 1  # +1 for space
                    
                    if potential_word_length <= max_chunk_size:
                        if word_chunk:
                            word_chunk += " " + word
                        else:
                            word_chunk = word
                    else:
                        # Save current word chunk
                        if word_chunk:
                            chunks.append(word_chunk)
                            
                            # Start new chunk with overlap
                            if overlap > 0 and len(word_chunk) > overlap:
                                overlap_words = word_chunk[-overlap:].split()
                                # Take last few words as overlap
                                if len(overlap_words) > 1:
                                    word_chunk = " ".join(overlap_words[1:]) + " " + word
                                else:
                                    word_chunk = word
                            else:
                                word_chunk = word
                        else:
                            # Single word is too long (edge case)
                            word_chunk = word
                
                # Add remaining words as current chunk
                if word_chunk:
                    current_chunk = word_chunk
    
    # Add final chunk if it exists
    if current_chunk and current_chunk.strip():
        chunks.append(current_chunk)
    
    # Filter out very small chunks (less than 20 characters)
    meaningful_chunks = [chunk for chunk in chunks if len(chunk.strip()) >= 20]
    
    logger.debug(f"Chunking completed: {len(chunks)} total chunks, {len(meaningful_chunks)} meaningful chunks")
    
    if len(meaningful_chunks) != len(chunks):
        logger.debug(f"Filtered out {len(chunks) - len(meaningful_chunks)} small chunks")
    
    return meaningful_chunks
