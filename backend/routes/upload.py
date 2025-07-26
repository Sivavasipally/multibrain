"""
File upload routes for RAG Chatbot PWA
"""

import os
import zipfile
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
# Note: This route file is not currently used by app_local.py
# The models are defined in app_local.py, not in a separate models.py file
# We use TextChunk instead of Document model
from models import db, Context, TextChunk
# from tasks.file_processor import process_uploaded_files_task  # Disabled for local version

upload_bp = Blueprint('upload', __name__)

# Supported file extensions
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

ALL_EXTENSIONS = [ext for exts in SUPPORTED_EXTENSIONS.values() for ext in exts]

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALL_EXTENSIONS

def get_file_category(filename):
    """Get file category based on extension"""
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return category
    return 'unknown'

@upload_bp.route('/files', methods=['POST'])
@jwt_required()
def upload_files():
    """Upload files for processing"""
    try:
        user_id = get_jwt_identity()
        
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        context_id = request.form.get('context_id')
        
        if not context_id:
            return jsonify({'error': 'Context ID is required'}), 400
        
        # Verify context ownership
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        if context.source_type != 'files':
            return jsonify({'error': 'Context is not configured for file uploads'}), 400
        
        uploaded_files = []
        upload_folder = current_app.config['UPLOAD_FOLDER']
        context_folder = os.path.join(upload_folder, f'context_{context_id}')
        os.makedirs(context_folder, exist_ok=True)
        
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                return jsonify({'error': f'File type not supported: {file.filename}'}), 400
            
            # Secure filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(context_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(file_path):
                filename = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(context_folder, filename)
                counter += 1
            
            # Save file
            file.save(file_path)
            
            # Create document record
            document = Document(
                context_id=context_id,
                filename=filename,
                file_path=file_path,
                file_type=get_file_category(filename),
                file_size=os.path.getsize(file_path)
            )
            
            db.session.add(document)
            uploaded_files.append({
                'filename': filename,
                'size': document.file_size,
                'type': document.file_type
            })
        
        db.session.commit()
        
        # Start background processing
        if uploaded_files:
            process_uploaded_files_task.delay(context_id)
        
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_files)} files',
            'files': uploaded_files
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/extract-zip', methods=['POST'])
@jwt_required()
def extract_zip():
    """Extract and process ZIP archive"""
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        context_id = request.form.get('context_id')
        
        if not context_id:
            return jsonify({'error': 'Context ID is required'}), 400
        
        # Verify context ownership
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        
        if not file.filename.lower().endswith('.zip'):
            return jsonify({'error': 'Only ZIP files are supported'}), 400
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        context_folder = os.path.join(upload_folder, f'context_{context_id}')
        os.makedirs(context_folder, exist_ok=True)
        
        # Save ZIP file temporarily
        zip_path = os.path.join(context_folder, 'temp.zip')
        file.save(zip_path)
        
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.is_dir():
                        continue
                    
                    # Check file extension
                    if not allowed_file(file_info.filename):
                        continue
                    
                    # Extract file
                    extracted_path = zip_ref.extract(file_info, context_folder)
                    
                    # Create document record
                    filename = os.path.basename(file_info.filename)
                    document = Document(
                        context_id=context_id,
                        filename=filename,
                        file_path=extracted_path,
                        file_type=get_file_category(filename),
                        file_size=file_info.file_size
                    )
                    
                    db.session.add(document)
                    extracted_files.append({
                        'filename': filename,
                        'size': document.file_size,
                        'type': document.file_type
                    })
            
            # Remove temporary ZIP file
            os.remove(zip_path)
            
        except zipfile.BadZipFile:
            return jsonify({'error': 'Invalid ZIP file'}), 400
        
        db.session.commit()
        
        # Start background processing
        if extracted_files:
            process_uploaded_files_task.delay(context_id)
        
        return jsonify({
            'message': f'Successfully extracted {len(extracted_files)} files',
            'files': extracted_files
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/supported-extensions', methods=['GET'])
def get_supported_extensions():
    """Get list of supported file extensions"""
    return jsonify({
        'extensions': SUPPORTED_EXTENSIONS,
        'total_count': len(ALL_EXTENSIONS)
    }), 200
