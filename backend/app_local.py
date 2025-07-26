"""
Local development version of the RAG Chatbot PWA
Simplified setup without Docker, Redis, or complex dependencies
"""

import os
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import re
from pathlib import Path
import mimetypes

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
import secrets
default_secret = secrets.token_urlsafe(32)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', default_secret)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ragchatbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', default_secret)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '104857600'))  # 100MB

# Import models and use their db instance
from models import db, User, Context, Document, ChatSession, Message, TextChunk

# Initialize the db with the app
db.init_app(app)

# Initialize other extensions
jwt = JWTManager(app)
CORS(app, origins=[
    os.getenv('FRONTEND_URL', 'http://localhost:5173'),
    'http://localhost:5173',
    'http://localhost:5174'
])

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to get user ID as integer from JWT
def get_current_user_id():
    """Get the current user ID as an integer from JWT token"""
    user_id_str = get_jwt_identity()
    return int(user_id_str) if user_id_str else None

# Text processing functions
def extract_text_from_file(file_path):
    """Extract text from various file types with language-specific handling"""
    file_extension = Path(file_path).suffix.lower()
    file_name = Path(file_path).name

    try:
        # Handle binary file types first
        if file_extension == '.pdf':
            return extract_pdf_content(file_path, file_name)
        elif file_extension in ['.xlsx', '.xls']:
            return extract_excel_content(file_path, file_name)
        elif file_extension in ['.docx', '.doc']:
            return extract_docx_content(file_path, file_name)

        # Handle text-based files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        # Add language-specific metadata and formatting
        if file_extension in ['.py']:
            return format_python_content(content, file_name)
        elif file_extension in ['.js', '.ts']:
            return format_javascript_content(content, file_name)
        elif file_extension in ['.java']:
            return format_java_content(content, file_name)
        elif file_extension in ['.cpp', '.c', '.h', '.hpp']:
            return format_cpp_content(content, file_name)
        elif file_extension in ['.go']:
            return format_go_content(content, file_name)
        elif file_extension in ['.rs']:
            return format_rust_content(content, file_name)
        elif file_extension == '.md':
            return format_markdown_content(content, file_name)
        elif file_extension in ['.json', '.yaml', '.yml']:
            return format_config_content(content, file_name, file_extension)
        elif file_extension == '.csv':
            return format_csv_content(content, file_name)
        elif file_extension == '.txt':
            return f"# {file_name}\n\n{content}"
        else:
            # For other file types, add basic formatting
            return f"# {file_name}\nFile Type: {file_extension}\n\n{content}"

    except Exception as e:
        return f"# {file_name}\nError reading file {file_path}: {str(e)}"

def extract_pdf_content(file_path, file_name):
    """Extract text from PDF files using PyMuPDF"""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        text_content = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                text_content.append(f"## Page {page_num + 1}\n\n{text}")

        doc.close()

        full_content = f"# PDF Document: {file_name}\n\n" + "\n\n".join(text_content)
        return full_content

    except ImportError:
        return f"# PDF Document: {file_name}\n\nError: PyMuPDF not installed. Cannot extract PDF content."
    except Exception as e:
        return f"# PDF Document: {file_name}\n\nError extracting PDF content: {str(e)}"

def extract_excel_content(file_path, file_name):
    """Extract content from Excel files"""
    try:
        import pandas as pd

        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        content_parts = [f"# Excel File: {file_name}\n"]

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            content_parts.append(f"\n## Sheet: {sheet_name}")
            content_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            content_parts.append(f"Columns: {', '.join(df.columns.tolist())}")

            # Add sample data (first 5 rows)
            if len(df) > 0:
                content_parts.append("\n### Sample Data:")
                content_parts.append(df.head().to_string())

            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                content_parts.append("\n### Numeric Summary:")
                content_parts.append(df[numeric_cols].describe().to_string())

        return "\n".join(content_parts)

    except ImportError:
        return f"# Excel File: {file_name}\n\nError: pandas not installed. Cannot extract Excel content."
    except Exception as e:
        return f"# Excel File: {file_name}\n\nError extracting Excel content: {str(e)}"

def extract_docx_content(file_path, file_name):
    """Extract content from Word documents"""
    try:
        from docx import Document

        doc = Document(file_path)
        content_parts = [f"# Word Document: {file_name}\n"]

        # Extract paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                content_parts.append(para.text)

        # Extract tables
        for table in doc.tables:
            content_parts.append("\n## Table:")
            for row in table.rows:
                row_text = " | ".join([cell.text for cell in row.cells])
                content_parts.append(row_text)

        return "\n".join(content_parts)

    except ImportError:
        return f"# Word Document: {file_name}\n\nError: python-docx not installed. Cannot extract Word content."
    except Exception as e:
        return f"# Word Document: {file_name}\n\nError extracting Word content: {str(e)}"

def format_csv_content(content, file_name):
    """Format CSV content with analysis"""
    try:
        import pandas as pd
        from io import StringIO

        df = pd.read_csv(StringIO(content))

        formatted = f"# CSV File: {file_name}\n\n"
        formatted += f"## Dataset Information\n"
        formatted += f"- Rows: {len(df)}\n"
        formatted += f"- Columns: {len(df.columns)}\n"
        formatted += f"- Column Names: {', '.join(df.columns.tolist())}\n\n"

        # Add sample data
        formatted += f"## Sample Data (First 5 Rows)\n"
        formatted += df.head().to_string() + "\n\n"

        # Add data types
        formatted += f"## Data Types\n"
        for col, dtype in df.dtypes.items():
            formatted += f"- {col}: {dtype}\n"

        # Add summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            formatted += f"\n## Numeric Summary\n"
            formatted += df[numeric_cols].describe().to_string()

        formatted += f"\n\n## Full Data\n```csv\n{content}\n```"

        return formatted

    except Exception as e:
        return f"# CSV File: {file_name}\n\nError processing CSV: {str(e)}\n\n## Raw Content\n```csv\n{content}\n```"

def format_python_content(content, file_name):
    """Format Python code with documentation extraction"""
    formatted = f"# Python File: {file_name}\n\n"

    # Extract docstrings and comments
    lines = content.split('\n')
    in_docstring = False
    docstring_content = []

    for line in lines:
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            if in_docstring:
                in_docstring = False
                if docstring_content:
                    formatted += "## Documentation:\n" + '\n'.join(docstring_content) + "\n\n"
                    docstring_content = []
            else:
                in_docstring = True
        elif in_docstring:
            docstring_content.append(stripped)
        elif stripped.startswith('#'):
            formatted += f"## Comment: {stripped[1:].strip()}\n"

    formatted += f"\n## Full Code:\n```python\n{content}\n```"
    return formatted

def format_javascript_content(content, file_name):
    """Format JavaScript/TypeScript code with documentation extraction"""
    formatted = f"# JavaScript/TypeScript File: {file_name}\n\n"

    # Extract JSDoc comments and regular comments
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('/**') or stripped.startswith('*') or stripped.startswith('//'):
            formatted += f"## Documentation: {stripped}\n"

    formatted += f"\n## Full Code:\n```javascript\n{content}\n```"
    return formatted

def format_java_content(content, file_name):
    """Format Java code with documentation extraction"""
    formatted = f"# Java File: {file_name}\n\n"

    # Extract class and method information
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if 'class ' in stripped and 'public' in stripped:
            formatted += f"## Class: {stripped}\n"
        elif 'public ' in stripped and '(' in stripped:
            formatted += f"## Method: {stripped}\n"
        elif stripped.startswith('/**') or stripped.startswith('*') or stripped.startswith('//'):
            formatted += f"## Documentation: {stripped}\n"

    formatted += f"\n## Full Code:\n```java\n{content}\n```"
    return formatted

def format_cpp_content(content, file_name):
    """Format C/C++ code with documentation extraction"""
    formatted = f"# C/C++ File: {file_name}\n\n"

    # Extract function declarations and comments
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*'):
            formatted += f"## Documentation: {stripped}\n"
        elif '(' in stripped and ('{' in stripped or ';' in stripped):
            formatted += f"## Function: {stripped}\n"

    formatted += f"\n## Full Code:\n```cpp\n{content}\n```"
    return formatted

def format_go_content(content, file_name):
    """Format Go code with documentation extraction"""
    formatted = f"# Go File: {file_name}\n\n"

    # Extract package, function, and comment information
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('package '):
            formatted += f"## Package: {stripped}\n"
        elif stripped.startswith('func '):
            formatted += f"## Function: {stripped}\n"
        elif stripped.startswith('//'):
            formatted += f"## Documentation: {stripped}\n"

    formatted += f"\n## Full Code:\n```go\n{content}\n```"
    return formatted

def format_rust_content(content, file_name):
    """Format Rust code with documentation extraction"""
    formatted = f"# Rust File: {file_name}\n\n"

    # Extract function, struct, and comment information
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('fn '):
            formatted += f"## Function: {stripped}\n"
        elif stripped.startswith('struct '):
            formatted += f"## Struct: {stripped}\n"
        elif stripped.startswith('//') or stripped.startswith('///'):
            formatted += f"## Documentation: {stripped}\n"

    formatted += f"\n## Full Code:\n```rust\n{content}\n```"
    return formatted

def format_markdown_content(content, file_name):
    """Format Markdown content with structure preservation"""
    return f"# Markdown Document: {file_name}\n\n{content}"

def format_config_content(content, file_name, file_extension):
    """Format configuration files"""
    formatted = f"# Configuration File: {file_name}\n"
    formatted += f"Type: {file_extension.upper()}\n\n"
    formatted += f"## Configuration Content:\n```{file_extension[1:]}\n{content}\n```"
    return formatted

def chunk_text(text, chunk_size=1000, chunk_overlap=200, chunk_strategy='language-specific', file_extension=None):
    """Split text into chunks using different strategies"""
    if len(text) <= chunk_size:
        return [text]

    if chunk_strategy == 'language_specific' and file_extension:
        return chunk_by_language(text, file_extension, chunk_size, chunk_overlap)
    elif chunk_strategy == 'semantic':
        return chunk_semantically(text, chunk_size, chunk_overlap)
    else:
        return chunk_by_size(text, chunk_size, chunk_overlap)

def chunk_by_language(text, file_extension, chunk_size=1000, chunk_overlap=200):
    """Language-specific chunking for code files"""
    if file_extension in ['.py']:
        return chunk_python_code(text, chunk_size, chunk_overlap)
    elif file_extension in ['.js', '.ts']:
        return chunk_javascript_code(text, chunk_size, chunk_overlap)
    elif file_extension in ['.java']:
        return chunk_java_code(text, chunk_size, chunk_overlap)
    elif file_extension in ['.cpp', '.c', '.h', '.hpp']:
        return chunk_cpp_code(text, chunk_size, chunk_overlap)
    elif file_extension in ['.go']:
        return chunk_go_code(text, chunk_size, chunk_overlap)
    elif file_extension in ['.rs']:
        return chunk_rust_code(text, chunk_size, chunk_overlap)
    elif file_extension == '.md':
        return chunk_markdown(text, chunk_size, chunk_overlap)
    else:
        return chunk_semantically(text, chunk_size, chunk_overlap)

def chunk_python_code(text, chunk_size, chunk_overlap):
    """Chunk Python code by functions, classes, and logical blocks"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for function or class definitions
        if line.strip().startswith(('def ', 'class ', 'async def ')):
            # If we have content, save current chunk
            if current_chunk and current_size > chunk_size // 2:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            # Add the function/class definition and its body
            current_chunk.append(line)
            current_size += len(line)
            i += 1

            # Get the indentation level
            indent_level = len(line) - len(line.lstrip())

            # Add all lines that belong to this function/class
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip() == '':
                    current_chunk.append(next_line)
                    current_size += len(next_line)
                    i += 1
                elif len(next_line) - len(next_line.lstrip()) > indent_level:
                    current_chunk.append(next_line)
                    current_size += len(next_line)
                    i += 1
                else:
                    break
        else:
            current_chunk.append(line)
            current_size += len(line)
            i += 1

            # If chunk is getting too large, split it
            if current_size > chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

    # Add remaining content
    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks if chunks else [text]

def chunk_javascript_code(text, chunk_size, chunk_overlap):
    """Chunk JavaScript/TypeScript code by functions and classes"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0
    brace_count = 0

    for line in lines:
        current_chunk.append(line)
        current_size += len(line)

        # Count braces to track function/class boundaries
        brace_count += line.count('{') - line.count('}')

        # If we're at a function/class boundary and chunk is large enough
        if brace_count == 0 and current_size > chunk_size // 2:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        elif current_size > chunk_size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
            brace_count = 0

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks if chunks else [text]

def chunk_java_code(text, chunk_size, chunk_overlap):
    """Chunk Java code by methods and classes"""
    return chunk_javascript_code(text, chunk_size, chunk_overlap)  # Similar structure

def chunk_cpp_code(text, chunk_size, chunk_overlap):
    """Chunk C/C++ code by functions"""
    return chunk_javascript_code(text, chunk_size, chunk_overlap)  # Similar structure

def chunk_go_code(text, chunk_size, chunk_overlap):
    """Chunk Go code by functions and structs"""
    return chunk_javascript_code(text, chunk_size, chunk_overlap)  # Similar structure

def chunk_rust_code(text, chunk_size, chunk_overlap):
    """Chunk Rust code by functions and structs"""
    return chunk_javascript_code(text, chunk_size, chunk_overlap)  # Similar structure

def chunk_markdown(text, chunk_size, chunk_overlap):
    """Chunk Markdown by headers and sections"""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0

    for line in lines:
        # If we hit a header and current chunk is substantial
        if line.startswith('#') and current_chunk and current_size > chunk_size // 2:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = len(line)
        else:
            current_chunk.append(line)
            current_size += len(line)

            if current_size > chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks if chunks else [text]

def chunk_semantically(text, chunk_size, chunk_overlap):
    """Semantic chunking by paragraphs and sentences"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at paragraph boundaries first
        if end < len(text):
            paragraph_end = text.rfind('\n\n', start, end)
            if paragraph_end > start + chunk_size // 2:
                end = paragraph_end + 2
            else:
                # Try sentence boundaries
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size - 100:
                    end = sentence_end + 1
                else:
                    # Fall back to word boundaries
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + chunk_size - 50:
                        end = word_end

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap
        if start >= len(text):
            break

    return chunks

def chunk_by_size(text, chunk_size, chunk_overlap):
    """Simple size-based chunking"""
    return chunk_semantically(text, chunk_size, chunk_overlap)

def generate_intelligent_response(query, relevant_chunks, all_chunks):
    """Generate intelligent responses based on document content"""
    query_lower = query.lower()

    # Check for summary/overview requests
    summary_keywords = {'summary', 'summarize', 'overview', 'main points', 'key points', 'what is', 'about', 'describe'}
    is_summary_request = any(keyword in query_lower for keyword in summary_keywords)

    if not relevant_chunks and not all_chunks:
        return "I don't have any documents to analyze. Please upload some documents to your context first."

    if is_summary_request and all_chunks:
        return generate_document_summary(all_chunks)
    elif relevant_chunks:
        return generate_contextual_response(query, relevant_chunks)
    else:
        return f"I couldn't find specific information about '{query}' in your uploaded documents. Try rephrasing your question or asking for a general summary."

def generate_document_summary(all_chunks):
    """Generate a comprehensive summary of all documents"""
    if not all_chunks:
        return "No documents found to summarize."

    # Group chunks by file
    files_content = {}
    for chunk in all_chunks:
        file_name = chunk['file_name']
        if file_name not in files_content:
            files_content[file_name] = []
        files_content[file_name].append(chunk['content'])

    summary_parts = ["📄 **Document Summary**\n"]

    for file_name, chunks in files_content.items():
        # Combine all chunks for this file
        full_content = ' '.join(chunks)

        # Extract key information
        key_points = extract_key_points(full_content)

        summary_parts.append(f"\n**📁 {file_name}:**")
        if key_points:
            for point in key_points[:3]:  # Top 3 key points per file
                summary_parts.append(f"• {point}")
        else:
            # Fallback: use first chunk as summary
            first_chunk = chunks[0][:300] + "..." if len(chunks[0]) > 300 else chunks[0]
            summary_parts.append(f"• {first_chunk}")

    # Add overall statistics
    total_files = len(files_content)
    total_chunks = len(all_chunks)

    summary_parts.append(f"\n📊 **Statistics:**")
    summary_parts.append(f"• Total files: {total_files}")
    summary_parts.append(f"• Total sections: {total_chunks}")

    return '\n'.join(summary_parts)

def generate_contextual_response(query, relevant_chunks):
    """Generate response based on relevant chunks"""
    if not relevant_chunks:
        return f"I couldn't find specific information about '{query}' in your documents."

    response_parts = [f"📋 **Based on your documents, here's what I found about '{query}':**\n"]

    # Group by file for better organization
    files_info = {}
    for chunk in relevant_chunks[:5]:  # Top 5 most relevant chunks
        file_name = chunk['file_name']
        if file_name not in files_info:
            files_info[file_name] = []
        files_info[file_name].append(chunk['content'])

    for file_name, contents in files_info.items():
        response_parts.append(f"\n**📁 From {file_name}:**")
        for content in contents:
            # Truncate long content but keep it meaningful
            if len(content) > 400:
                content = content[:400] + "..."
            response_parts.append(f"• {content}")

    return '\n'.join(response_parts)

def extract_key_points(text):
    """Extract key points from text using simple heuristics"""
    if not text:
        return []

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    key_points = []

    # Look for sentences that might be key points
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 200:
            continue

        # Prioritize sentences with key indicators
        key_indicators = ['purpose', 'goal', 'objective', 'main', 'key', 'important', 'summary', 'overview']
        if any(indicator in sentence.lower() for indicator in key_indicators):
            key_points.append(sentence)
        elif len(key_points) < 3:  # Add first few sentences as fallback
            key_points.append(sentence)

    return key_points[:5]  # Return top 5 key points

def generate_vector_search_response(query, context_ids):
    """Generate response using vector search for repository contexts"""
    try:
        from services.gemini_service import GeminiService
        import faiss
        import numpy as np

        # Initialize services
        gemini_service = GeminiService()

        # Create query embedding
        query_embedding = gemini_service.create_query_embedding(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)

        # Search across all context vector stores
        all_results = []

        for context_id in context_ids:
            try:
                # Load FAISS index
                vector_store_dir = os.path.join('vector_stores', str(context_id))
                index_path = os.path.join(vector_store_dir, 'index.faiss')
                metadata_path = os.path.join(vector_store_dir, 'metadata.json')

                if not os.path.exists(index_path) or not os.path.exists(metadata_path):
                    continue

                # Load index and metadata
                index = faiss.read_index(index_path)
                with open(metadata_path, 'r') as f:
                    chunks_metadata = json.load(f)

                # Search for similar chunks
                k = min(5, index.ntotal)  # Top 5 or all available
                scores, indices = index.search(query_vector, k)

                # Collect results
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(chunks_metadata) and score > 0.3:  # Similarity threshold
                        chunk_data = chunks_metadata[idx]
                        all_results.append({
                            'content': chunk_data['content'],
                            'source': chunk_data['file_name'],
                            'score': float(score),
                            'context_id': context_id,
                            'metadata': chunk_data['metadata']
                        })

            except Exception as e:
                print(f"Error searching context {context_id}: {e}")
                continue

        # Sort by relevance score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        top_results = all_results[:10]  # Top 10 results

        if not top_results:
            return "I couldn't find relevant information in the repository code. Please try rephrasing your question or check if the repository has been processed correctly."

        # Generate response using Gemini
        response_data = gemini_service.generate_response(
            query=query,
            context_chunks=top_results,
            max_tokens=2048
        )

        # Format response with code context
        formatted_response = f"🔍 **Based on the repository code analysis:**\n\n{response_data['content']}\n\n"

        # Add source references
        if top_results:
            formatted_response += "📁 **Sources:**\n"
            seen_sources = set()
            for result in top_results[:5]:
                source = result['source']
                if source not in seen_sources:
                    language = result['metadata'].get('language', 'unknown')
                    formatted_response += f"• `{source}` ({language})\n"
                    seen_sources.add(source)

        return formatted_response

    except Exception as e:
        print(f"Error in vector search response: {e}")
        return f"I encountered an error while searching the repository: {str(e)}. Please try again or check if the repository has been processed correctly."

def process_context_files(context_id, file_paths, chunk_strategy='language-specific'):
    """Process uploaded files and create chunks with language-specific handling"""
    all_chunks = []

    for file_path in file_paths:
        try:
            # Extract text from file with language-specific formatting
            text = extract_text_from_file(file_path)
            file_extension = Path(file_path).suffix.lower()
            file_name = Path(file_path).name

            # Determine chunk size based on file type
            if file_extension in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
                chunk_size = 1500  # Larger chunks for code files
                chunk_overlap = 300
            else:
                chunk_size = 1000  # Standard size for text files
                chunk_overlap = 200

            # Create chunks using specified strategy
            chunks = chunk_text(text, chunk_size, chunk_overlap, chunk_strategy, file_extension)

            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                # Analyze chunk content for additional metadata
                chunk_metadata = analyze_chunk_content(chunk, file_extension)

                chunk_data = {
                    'context_id': context_id,
                    'file_name': file_name,
                    'chunk_index': i,
                    'content': chunk,
                    'metadata': {
                        'file_path': file_path,
                        'file_type': file_extension,
                        'chunk_size': len(chunk),
                        'chunk_strategy': chunk_strategy,
                        'language': detect_language(file_extension),
                        'content_type': chunk_metadata['content_type'],
                        'has_code': chunk_metadata['has_code'],
                        'has_documentation': chunk_metadata['has_documentation'],
                        'complexity_score': chunk_metadata['complexity_score']
                    }
                }
                all_chunks.append(chunk_data)

        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            continue

    return all_chunks

def analyze_chunk_content(chunk, file_extension):
    """Analyze chunk content to extract metadata"""
    metadata = {
        'content_type': 'text',
        'has_code': False,
        'has_documentation': False,
        'complexity_score': 0
    }

    chunk_lower = chunk.lower()

    # Detect content type
    if file_extension in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
        metadata['content_type'] = 'code'
        metadata['has_code'] = True

        # Check for documentation
        if any(marker in chunk for marker in ['"""', "'''", '/**', '///', '##']):
            metadata['has_documentation'] = True

        # Simple complexity scoring
        complexity_indicators = ['if ', 'for ', 'while ', 'try ', 'catch ', 'function ', 'class ', 'def ']
        metadata['complexity_score'] = sum(chunk_lower.count(indicator) for indicator in complexity_indicators)

    elif file_extension == '.md':
        metadata['content_type'] = 'documentation'
        metadata['has_documentation'] = True

        # Count headers and lists for complexity
        metadata['complexity_score'] = chunk.count('#') + chunk.count('- ') + chunk.count('* ')

    elif file_extension in ['.json', '.yaml', '.yml']:
        metadata['content_type'] = 'configuration'
        metadata['complexity_score'] = chunk.count(':') + chunk.count('-')

    return metadata

def detect_language(file_extension):
    """Detect programming language from file extension"""
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.kt': 'kotlin',
        '.swift': 'swift',
        '.md': 'markdown',
        '.txt': 'text',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml'
    }

    return language_map.get(file_extension, 'unknown')

def process_repository_context(context_id, config):
    """Process repository context by cloning and analyzing code"""
    try:
        from services.repository_service import RepositoryService
        from services.gemini_service import GeminiService
        import faiss
        import numpy as np

        # Get context
        context = Context.query.get(context_id)
        if not context:
            print(f"Context {context_id} not found")
            return

        # Update status
        context.status = 'processing'
        context.progress = 10
        db.session.commit()

        # Get repository configuration - check multiple possible keys
        repo_url = config.get('repo_url') or config.get('url') or config.get('repository_url')
        branch = config.get('branch', 'main')

        print(f"Repository config received: {config}")
        print(f"Extracted repo_url: {repo_url}")
        print(f"Branch: {branch}")

        if not repo_url:
            context.status = 'error'
            context.error_message = f'Repository URL not provided. Config received: {config}'
            db.session.commit()
            return

        print(f"Processing repository: {repo_url}")

        # Clone repository
        repo_service = RepositoryService()
        clone_result = repo_service.clone_repository_direct(repo_url, branch)

        if not clone_result['success']:
            context.status = 'error'
            context.error_message = f"Failed to clone repository: {clone_result['error']}"
            db.session.commit()
            return

        context.progress = 30
        db.session.commit()

        # Get repository info and processable files
        repo_info = clone_result['repo_info']
        clone_path = clone_result['clone_path']
        processable_files = repo_info['file_analysis']['processable_files']

        print(f"Found {len(processable_files)} processable files")

        # Process files and create chunks
        chunk_strategy = config.get('chunk_strategy', 'language_specific')
        all_chunks = []

        for i, file_info in enumerate(processable_files[:50]):  # Limit to 50 files
            try:
                file_path = file_info['path']

                # Extract text from file
                text = extract_text_from_file(file_path)
                file_extension = Path(file_path).suffix.lower()

                # Create chunks
                chunks = chunk_text(text, 1500, 300, chunk_strategy, file_extension)

                # Add metadata to chunks
                for j, chunk in enumerate(chunks):
                    chunk_data = {
                        'context_id': context_id,
                        'file_name': file_info['relative_path'],
                        'chunk_index': j,
                        'content': chunk,
                        'metadata': {
                            'file_path': file_info['relative_path'],
                            'file_type': file_extension,
                            'language': file_info['language'],
                            'chunk_size': len(chunk),
                            'chunk_strategy': chunk_strategy,
                            'repository_url': repo_url,
                            'repository_branch': branch,
                            'project_type': repo_info['project_info']['primary_type']
                        }
                    }
                    all_chunks.append(chunk_data)

            except Exception as e:
                print(f"Error processing file {file_info['path']}: {e}")
                continue

            # Update progress
            progress = 30 + int((i / len(processable_files)) * 40)
            context.progress = progress
            db.session.commit()

        print(f"Created {len(all_chunks)} chunks")

        # Create embeddings and store in vector database
        if all_chunks:
            context.progress = 70
            db.session.commit()

            # Initialize Gemini service for embeddings
            gemini_service = GeminiService()

            # Create embeddings for chunks in batches
            chunk_texts = [chunk['content'] for chunk in all_chunks]
            print(f"Creating embeddings for {len(chunk_texts)} chunks...")

            # Process in smaller batches to avoid timeouts
            batch_size = 5
            embeddings = []

            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(chunk_texts) + batch_size - 1)//batch_size}")

                batch_embeddings = gemini_service.create_embeddings(batch, "retrieval_document")
                embeddings.extend(batch_embeddings)

                # Update progress
                progress = 70 + int((i / len(chunk_texts)) * 15)
                context.progress = progress
                db.session.commit()

            # Create FAISS index
            embedding_dim = len(embeddings[0]) if embeddings else 768
            index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity

            # Normalize embeddings and add to index
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            index.add(embeddings_array)

            # Save FAISS index
            vector_store_dir = os.path.join('vector_stores', str(context_id))
            os.makedirs(vector_store_dir, exist_ok=True)
            vector_store_path = os.path.join(vector_store_dir, 'index.faiss')
            faiss.write_index(index, vector_store_path)

            # Save chunk metadata
            metadata_path = os.path.join(vector_store_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(all_chunks, f, indent=2)

            context.progress = 90
            db.session.commit()

        # Store chunks in database
        for chunk_data in all_chunks:
            chunk = TextChunk(
                context_id=chunk_data['context_id'],
                file_name=chunk_data['file_name'],
                chunk_index=chunk_data['chunk_index'],
                content=chunk_data['content']
            )
            chunk.set_file_info(chunk_data['metadata'])
            db.session.add(chunk)

        # Update context with final statistics
        context.total_chunks = len(all_chunks)
        context.total_tokens = sum(len(chunk['content'].split()) for chunk in all_chunks)
        context.status = 'ready'
        context.progress = 100
        db.session.commit()

        # Cleanup cloned repository
        repo_service.cleanup_repository(clone_path)

        print(f"Repository processing completed for context {context_id}")

    except Exception as e:
        print(f"Error processing repository context {context_id}: {e}")
        context = Context.query.get(context_id)
        if context:
            context.status = 'error'
            context.error_message = str(e)
            db.session.commit()

# User model is imported from models.py

# Simple Context model
# Context model is imported from models.py - no need to redefine here

# ChatSession model is imported from models.py

# Message model is imported from models.py
# TextChunk model is imported from models.py

# Routes

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create access token (convert user.id to string)
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user': user.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts', methods=['GET'])
@jwt_required()
def get_contexts():
    try:
        user_id = get_current_user_id()
        contexts = Context.query.filter_by(user_id=user_id).all()
        return jsonify({'contexts': [ctx.to_dict() for ctx in contexts]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts', methods=['POST'])
@jwt_required()
def create_context():
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Extract configuration values
        chunk_strategy = data.get('chunk_strategy', 'language-specific')
        embedding_model = data.get('embedding_model', 'text-embedding-004')

        context = Context(
            name=data.get('name'),
            description=data.get('description', ''),
            source_type=data.get('source_type'),
            chunk_strategy=chunk_strategy,
            embedding_model=embedding_model,
            user_id=user_id,
            status='pending'  # Start as pending for processing
        )

        # Set the full configuration including source-specific config
        full_config = data.get('config', {})
        full_config.update({
            'chunk_strategy': chunk_strategy,
            'embedding_model': embedding_model
        })
        context.set_config(full_config)

        db.session.add(context)
        db.session.commit()

        # Process repository if source type is repo
        if data.get('source_type') == 'repo':
            # Extract repository config from the data
            repo_config = data.get('repo_config', {})
            if not repo_config and data.get('config'):
                # Fallback to config if repo_config is not present
                repo_config = data.get('config', {})
            process_repository_context(context.id, repo_config)

        return jsonify({'context': context.to_dict()}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts/<int:context_id>', methods=['GET'])
@jwt_required()
def get_context(context_id):
    try:
        user_id = get_current_user_id()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()

        if not context:
            return jsonify({'error': 'Context not found'}), 404

        # Get chunks for this context
        chunks = TextChunk.query.filter_by(context_id=context_id).all()

        # Group chunks by file to create documents data
        documents = {}
        for chunk in chunks:
            file_name = chunk.file_name
            if file_name not in documents:
                documents[file_name] = {
                    'id': f"{context_id}_{file_name}",
                    'filename': file_name,
                    'file_type': chunk.get_file_info().get('file_type', 'unknown'),
                    'file_size': chunk.get_file_info().get('chunk_size', 0),
                    'chunks_count': 0,
                    'tokens_count': 0,
                    'language': None,
                    'processed_at': chunk.created_at.isoformat()
                }
            documents[file_name]['chunks_count'] += 1
            documents[file_name]['tokens_count'] += len(chunk.content.split())

        context_data = context.to_dict()
        context_data['documents'] = list(documents.values())
        context_data['chunks'] = [chunk.to_dict() for chunk in chunks]

        return jsonify({'context': context_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts/<int:context_id>', methods=['PUT'])
@jwt_required()
def update_context(context_id):
    try:
        user_id = get_jwt_identity()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()

        if not context:
            return jsonify({'error': 'Context not found'}), 404

        data = request.get_json()
        if 'name' in data:
            context.name = data['name']
        if 'description' in data:
            context.description = data['description']

        db.session.commit()
        return jsonify({'context': context.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts/<int:context_id>', methods=['DELETE'])
@jwt_required()
def delete_context(context_id):
    try:
        user_id = get_current_user_id()

        # Get context and verify ownership
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            return jsonify({'error': 'Context not found'}), 404

        cleanup_stats = {
            'vector_stores_deleted': 0,
            'documents_deleted': 0,
            'files_deleted': 0,
            'chunks_deleted': 0
        }

        try:
            # Delete vector store files if they exist
            vector_store_dir = os.path.join('vector_stores', str(context_id))
            if os.path.exists(vector_store_dir):
                import shutil
                shutil.rmtree(vector_store_dir)
                cleanup_stats['vector_stores_deleted'] = 1
        except Exception as e:
            print(f"Error deleting vector store: {e}")

        try:
            # Delete uploaded files if they exist
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(context_id))
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)
                cleanup_stats['files_deleted'] = 1
        except Exception as e:
            print(f"Error deleting upload files: {e}")

        # Delete text chunks if they exist
        try:
            chunks_deleted = TextChunk.query.filter_by(context_id=context_id).delete()
            cleanup_stats['chunks_deleted'] = chunks_deleted
        except Exception as e:
            print(f"Error deleting chunks: {e}")

        # Delete the context (this will cascade delete documents)
        db.session.delete(context)
        db.session.commit()

        return jsonify({
            'message': f'Context "{context.name}" deleted successfully',
            'cleanup_stats': cleanup_stats
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error during context cleanup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts/<int:context_id>/reprocess', methods=['POST'])
@jwt_required()
def reprocess_context(context_id):
    try:
        user_id = get_jwt_identity()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()

        if not context:
            return jsonify({'error': 'Context not found'}), 404

        # Update context status to processing
        context.status = 'processing'
        context.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Here you would typically trigger the reprocessing job
        # For now, we'll just simulate it by updating the status
        # In a real implementation, you'd use a task queue like Celery

        return jsonify({
            'message': 'Context reprocessing started',
            'context': context.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts/<int:context_id>/status', methods=['GET'])
@jwt_required()
def get_context_status(context_id):
    try:
        user_id = get_jwt_identity()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()

        if not context:
            return jsonify({'error': 'Context not found'}), 404

        return jsonify({
            'status': context.status,
            'progress': context.progress,
            'error_message': context.error_message,
            'total_chunks': context.total_chunks,
            'total_tokens': context.total_tokens
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contexts/<int:context_id>/chunks', methods=['GET'])
@jwt_required()
def get_context_chunks(context_id):
    try:
        user_id = get_jwt_identity()
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()

        if not context:
            return jsonify({'error': 'Context not found'}), 404

        chunks = TextChunk.query.filter_by(context_id=context_id).order_by(TextChunk.file_name, TextChunk.chunk_index).all()

        return jsonify({
            'chunks': [chunk.to_dict() for chunk in chunks],
            'total_chunks': len(chunks)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    try:
        user_id = get_current_user_id()
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
        return jsonify({'sessions': [session.to_dict() for session in sessions]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        session = ChatSession(
            title=data.get('title', f'Chat {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
            user_id=user_id
        )
        
        db.session.add(session)
        db.session.commit()

        return jsonify({'session': session.to_dict()}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_chat_session(session_id):
    try:
        user_id = get_jwt_identity()
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()

        if not session:
            return jsonify({'error': 'Chat session not found'}), 404

        return jsonify({'session': session.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
def update_chat_session(session_id):
    try:
        user_id = get_jwt_identity()
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()

        if not session:
            return jsonify({'error': 'Chat session not found'}), 404

        data = request.get_json()
        if 'title' in data:
            session.title = data['title']

        db.session.commit()
        return jsonify({'session': session.to_dict()}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    try:
        user_id = get_jwt_identity()
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()

        if not session:
            return jsonify({'error': 'Chat session not found'}), 404

        db.session.delete(session)
        db.session.commit()
        return jsonify({'message': 'Chat session deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/query', methods=['POST'])
@jwt_required()
def chat_query():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        session_id = data.get('session_id')
        message_content = data.get('message')
        context_ids = data.get('context_ids', [])

        # Save user message
        user_message = Message(
            session_id=session_id,
            role='user',
            content=message_content
        )
        user_message.set_context_ids(context_ids)
        db.session.add(user_message)

        # Get relevant chunks from selected contexts
        relevant_chunks = []
        all_chunks = []

        if context_ids:
            for context_id in context_ids:
                # Verify user owns the context
                context = Context.query.filter_by(id=context_id, user_id=user_id).first()
                if context:
                    chunks = TextChunk.query.filter_by(context_id=context_id).all()

                    for chunk in chunks:
                        chunk_data = {
                            'content': chunk.content,
                            'file_name': chunk.file_name,
                            'context_name': context.name,
                            'chunk_index': chunk.chunk_index,
                            'relevance_score': 0
                        }
                        all_chunks.append(chunk_data)

                    # Enhanced relevance scoring
                    query_lower = message_content.lower()
                    query_words = set(query_lower.split())

                    # Check for summary/overview requests
                    summary_keywords = {'summary', 'summarize', 'overview', 'main points', 'key points', 'what is', 'about', 'describe'}
                    is_summary_request = any(keyword in query_lower for keyword in summary_keywords)

                    for chunk_data in all_chunks:
                        chunk_content_lower = chunk_data['content'].lower()

                        if is_summary_request:
                            # For summary requests, include all chunks but prioritize introductory content
                            chunk_data['relevance_score'] = 1.0
                            # Boost score for chunks that seem like introductions or overviews
                            if any(word in chunk_content_lower for word in ['introduction', 'overview', 'summary', 'abstract', 'purpose', 'goal']):
                                chunk_data['relevance_score'] = 2.0
                        else:
                            # For specific queries, use keyword matching with scoring
                            word_matches = sum(1 for word in query_words if word in chunk_content_lower)
                            if word_matches > 0:
                                chunk_data['relevance_score'] = word_matches / len(query_words)

                    # Sort by relevance and take top chunks
                    relevant_chunks = [chunk for chunk in all_chunks if chunk['relevance_score'] > 0]
                    relevant_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Use vector search for repository contexts
        contexts = [db.session.get(Context, cid) for cid in context_ids]
        contexts = [ctx for ctx in contexts if ctx is not None]  # Filter out None values
        if any(ctx.source_type == 'repo' for ctx in contexts):
            ai_response = generate_vector_search_response(message_content, context_ids)
        else:
            # Generate intelligent response based on query type and relevant chunks
            ai_response = generate_intelligent_response(message_content, relevant_chunks, all_chunks)

        assistant_message = Message(
            session_id=session_id,
            role='assistant',
            content=ai_response
        )
        assistant_message.set_context_ids(context_ids)
        db.session.add(assistant_message)

        # Update session timestamp
        session = db.session.get(ChatSession, session_id)
        if session:
            session.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({
            'message': assistant_message.to_dict(),
            'citations': []
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/files', methods=['POST'])
@jwt_required()
def upload_files():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        if 'context_id' not in request.form:
            return jsonify({'error': 'No context_id provided'}), 400

        context_id = request.form['context_id']
        user_id = get_current_user_id()

        # Verify context belongs to user
        context = Context.query.filter_by(id=context_id, user_id=user_id).first()
        if not context:
            return jsonify({'error': 'Context not found'}), 404

        files = request.files.getlist('files')
        uploaded_files = []
        file_paths = []

        # Save files first
        for file in files:
            if file.filename == '':
                continue

            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            uploaded_files.append({
                'filename': file.filename,  # Original filename
                'size': os.path.getsize(file_path),
                'path': file_path
            })
            file_paths.append(file_path)

        # Process files and create chunks
        if file_paths:
            context.status = 'processing'
            db.session.commit()

            try:
                # Get chunk strategy from context configuration
                context_config = context.get_config()
                chunk_strategy = context_config.get('chunk_strategy', context.chunk_strategy or 'language-specific')

                # Process files into chunks using the specified strategy
                chunks_data = process_context_files(context_id, file_paths, chunk_strategy)

                # Save chunks to database
                for chunk_data in chunks_data:
                    chunk = TextChunk(
                        context_id=chunk_data['context_id'],
                        file_name=chunk_data['file_name'],
                        chunk_index=chunk_data['chunk_index'],
                        content=chunk_data['content']
                    )
                    chunk.set_file_info(chunk_data['metadata'])
                    db.session.add(chunk)

                # Update context with chunk count
                context.total_chunks = len(chunks_data)
                context.total_tokens = sum(len(chunk['content'].split()) for chunk in chunks_data)
                context.status = 'ready'
                context.progress = 100

                db.session.commit()

                return jsonify({
                    'files': uploaded_files,
                    'chunks_created': len(chunks_data),
                    'total_tokens': context.total_tokens,
                    'status': 'ready'
                }), 200

            except Exception as e:
                context.status = 'error'
                context.error_message = str(e)
                db.session.commit()
                return jsonify({'error': f'Processing failed: {str(e)}'}), 500

        return jsonify({'files': uploaded_files}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/extract-zip', methods=['POST'])
@jwt_required()
def extract_zip():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No zip file provided'}), 400

        if 'context_id' not in request.form:
            return jsonify({'error': 'No context_id provided'}), 400

        zip_file = request.files['file']
        context_id = request.form['context_id']

        if zip_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # For now, just return a success message
        # In a real implementation, you would extract the zip file
        # and process its contents

        return jsonify({
            'message': 'Zip file extraction started',
            'files': [],
            'context_id': context_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/supported-extensions', methods=['GET'])
def get_supported_extensions():
    extensions = {
        'documents': ['.pdf', '.docx', '.doc', '.txt', '.md'],
        'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'],
        'data': ['.csv', '.json', '.yaml', '.yml', '.xml'],
        'archives': ['.zip', '.tar', '.gz']
    }
    
    total_count = sum(len(exts) for exts in extensions.values())
    
    return jsonify({
        'extensions': extensions,
        'total_count': total_count
    }), 200

# Health check
@app.route('/api/database/test-connection', methods=['POST'])
@jwt_required()
def test_database_connection():
    """Test database connection and return available tables"""
    try:
        from services.database_service import DatabaseService

        data = request.get_json()
        db_type = data.get('db_type')
        connection_string = data.get('connection_string')

        if not db_type or not connection_string:
            return jsonify({'error': 'Database type and connection string required'}), 400

        db_service = DatabaseService()
        result = db_service.test_connection(db_type, connection_string)

        if result['success']:
            # Get table list
            tables = db_service.get_table_list(db_type, connection_string)
            result['tables'] = tables

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': 'local-dev'
    }), 200

# Register route blueprints (only working ones for now)
from routes.admin import admin_bp
from routes.auth import auth_bp

app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# TODO: Fix and register other blueprints:
# - contexts_bp (has celery dependency issue)
# - chat_bp (may have service dependency issues)
# - upload_bp (needs model import fixes)

# Debug endpoint to check JWT token
@app.route('/api/debug/token', methods=['GET'])
@jwt_required()
def debug_token():
    try:
        user_id = get_jwt_identity()
        return jsonify({
            'status': 'Token is valid',
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Debug endpoint to check headers (no auth required)
@app.route('/api/debug/headers', methods=['GET'])
def debug_headers():
    headers = dict(request.headers)
    return jsonify({
        'headers': headers,
        'has_authorization': 'Authorization' in headers,
        'authorization_header': headers.get('Authorization', 'Not present')
    }), 200

# JWT Error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"JWT expired: {jwt_payload}")
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"JWT invalid: {error}")
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"JWT missing: {error}")
    print(f"Request headers: {dict(request.headers)}")
    return jsonify({'error': 'Authorization token is required'}), 401

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
        print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        print("Starting Flask development server...")

    # Run without debug mode to avoid watchdog issues
    app.run(debug=False, host='0.0.0.0', port=5000)
