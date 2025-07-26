"""
Document processing service with language-aware parsing
"""

import os
import ast
import json
import yaml
import fitz  # PyMuPDF
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser
import docx
from unstructured.partition.auto import partition

class DocumentProcessor:
    """Service for processing various document types with language-aware parsing"""
    
    def __init__(self):
        self.supported_extensions = {
            'text': ['.txt', '.md', '.rst', '.log'],
            'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.cs', '.kt', '.swift'],
            'document': ['.pdf', '.docx', '.doc', '.rtf'],
            'data': ['.csv', '.xlsx', '.xls', '.json', '.xml', '.yaml', '.yml'],
            'config': ['.ini', '.cfg', '.conf', '.toml', '.properties'],
            'web': ['.html', '.htm', '.css', '.scss', '.sass', '.less'],
            'sql': ['.sql', '.ddl', '.dml']
        }
        
        # Initialize tree-sitter parsers
        self.parsers = {}
        self._init_tree_sitter_parsers()
    
    def _init_tree_sitter_parsers(self):
        """Initialize tree-sitter parsers for supported languages"""
        try:
            # Note: In production, you'd need to build the language libraries
            # This is a simplified version
            language_configs = {
                'python': 'tree-sitter-python',
                'javascript': 'tree-sitter-javascript',
                'typescript': 'tree-sitter-typescript',
                'java': 'tree-sitter-java',
                'cpp': 'tree-sitter-cpp',
                'go': 'tree-sitter-go',
                'kotlin': 'tree-sitter-kotlin'
            }
            
            for lang, lib_name in language_configs.items():
                try:
                    # In production, you'd load the compiled language library
                    # language = Language(f'/path/to/{lib_name}.so', lang)
                    # parser = Parser()
                    # parser.set_language(language)
                    # self.parsers[lang] = parser
                    pass
                except Exception as e:
                    print(f"Warning: Could not load {lang} parser: {e}")
        
        except Exception as e:
            print(f"Warning: Tree-sitter initialization failed: {e}")
    
    def process_file(self, file_path: str, chunk_strategy: str = 'language-specific') -> List[Dict[str, Any]]:
        """Process a file and return chunks with metadata"""
        file_ext = Path(file_path).suffix.lower()
        file_type = self._get_file_type(file_ext)
        
        try:
            if file_type == 'code':
                return self._process_code_file(file_path, chunk_strategy)
            elif file_type == 'document':
                return self._process_document_file(file_path, chunk_strategy)
            elif file_type == 'data':
                return self._process_data_file(file_path, chunk_strategy)
            elif file_type == 'text':
                return self._process_text_file(file_path, chunk_strategy)
            elif file_type == 'config':
                return self._process_config_file(file_path, chunk_strategy)
            elif file_type == 'web':
                return self._process_web_file(file_path, chunk_strategy)
            elif file_type == 'sql':
                return self._process_sql_file(file_path, chunk_strategy)
            else:
                return self._process_generic_file(file_path, chunk_strategy)
        
        except Exception as e:
            return [{
                'content': f"Error processing file: {str(e)}",
                'metadata': {
                    'file_path': file_path,
                    'file_type': file_type,
                    'error': True,
                    'chunk_index': 0
                }
            }]
    
    def _get_file_type(self, extension: str) -> str:
        """Get file type category from extension"""
        for file_type, extensions in self.supported_extensions.items():
            if extension in extensions:
                return file_type
        return 'unknown'
    
    def _get_language_from_extension(self, extension: str) -> Optional[str]:
        """Get programming language from file extension"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.go': 'go',
            '.kt': 'kotlin',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift'
        }
        return language_map.get(extension)
    
    def _process_code_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process code files with language-aware parsing"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        file_ext = Path(file_path).suffix.lower()
        language = self._get_language_from_extension(file_ext)
        
        if language == 'python':
            return self._process_python_file(content, file_path)
        elif language in self.parsers:
            return self._process_with_tree_sitter(content, file_path, language)
        else:
            return self._process_code_generic(content, file_path, language)
    
    def _process_python_file(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Process Python files using AST"""
        chunks = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    # Extract function/class with docstring
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                    
                    lines = content.split('\n')
                    chunk_content = '\n'.join(lines[start_line-1:end_line])
                    
                    # Extract docstring
                    docstring = ast.get_docstring(node)
                    
                    chunks.append({
                        'content': chunk_content,
                        'metadata': {
                            'file_path': file_path,
                            'file_type': 'code',
                            'language': 'python',
                            'node_type': type(node).__name__,
                            'name': node.name,
                            'start_line': start_line,
                            'end_line': end_line,
                            'docstring': docstring,
                            'chunk_index': len(chunks)
                        }
                    })
            
            # If no functions/classes found, chunk by lines
            if not chunks:
                return self._chunk_by_lines(content, file_path, 'python')
        
        except SyntaxError:
            # Fallback to line-based chunking for invalid Python
            return self._chunk_by_lines(content, file_path, 'python')
        
        return chunks
    
    def _process_with_tree_sitter(self, content: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Process code using tree-sitter (placeholder implementation)"""
        # This would use tree-sitter to parse the code and extract functions, classes, etc.
        # For now, fall back to generic code processing
        return self._process_code_generic(content, file_path, language)
    
    def _process_code_generic(self, content: str, file_path: str, language: Optional[str]) -> List[Dict[str, Any]]:
        """Generic code processing by logical blocks"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                if current_chunk:
                    current_chunk.append(line)
                continue
            
            # Detect function/class definitions
            if any(stripped.startswith(keyword) for keyword in ['def ', 'class ', 'function ', 'interface ', 'struct ']):
                # Save previous chunk
                if current_chunk:
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'metadata': {
                            'file_path': file_path,
                            'file_type': 'code',
                            'language': language,
                            'chunk_index': len(chunks),
                            'start_line': i - len(current_chunk) + 1,
                            'end_line': i
                        }
                    })
                
                # Start new chunk
                current_chunk = [line]
                current_indent = len(line) - len(line.lstrip())
            
            elif current_chunk:
                # Continue current chunk
                current_chunk.append(line)
                
                # Check if we should end the chunk (dedent)
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= current_indent and len(current_chunk) > 20:
                    chunks.append({
                        'content': '\n'.join(current_chunk),
                        'metadata': {
                            'file_path': file_path,
                            'file_type': 'code',
                            'language': language,
                            'chunk_index': len(chunks),
                            'start_line': i - len(current_chunk) + 1,
                            'end_line': i
                        }
                    })
                    current_chunk = []
            else:
                current_chunk = [line]
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'code',
                    'language': language,
                    'chunk_index': len(chunks),
                    'start_line': len(lines) - len(current_chunk) + 1,
                    'end_line': len(lines)
                }
            })
        
        return chunks
    
    def _process_document_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process document files (PDF, DOCX, etc.)"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self._process_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self._process_docx(file_path)
        else:
            # Use unstructured.io for other document types
            return self._process_with_unstructured(file_path)
    
    def _process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Process PDF files using PyMuPDF"""
        chunks = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    chunks.append({
                        'content': text,
                        'metadata': {
                            'file_path': file_path,
                            'file_type': 'document',
                            'page_number': page_num + 1,
                            'chunk_index': len(chunks)
                        }
                    })
            
            doc.close()
        
        except Exception as e:
            chunks.append({
                'content': f"Error processing PDF: {str(e)}",
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'document',
                    'error': True,
                    'chunk_index': 0
                }
            })
        
        return chunks
    
    def _process_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Process DOCX files"""
        chunks = []
        
        try:
            doc = docx.Document(file_path)
            
            current_chunk = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    current_chunk.append(paragraph.text)
                    
                    # Create chunk every 10 paragraphs or when we hit a heading
                    if len(current_chunk) >= 10 or paragraph.style.name.startswith('Heading'):
                        if current_chunk:
                            chunks.append({
                                'content': '\n'.join(current_chunk),
                                'metadata': {
                                    'file_path': file_path,
                                    'file_type': 'document',
                                    'chunk_index': len(chunks)
                                }
                            })
                            current_chunk = []
            
            # Add final chunk
            if current_chunk:
                chunks.append({
                    'content': '\n'.join(current_chunk),
                    'metadata': {
                        'file_path': file_path,
                        'file_type': 'document',
                        'chunk_index': len(chunks)
                    }
                })
        
        except Exception as e:
            chunks.append({
                'content': f"Error processing DOCX: {str(e)}",
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'document',
                    'error': True,
                    'chunk_index': 0
                }
            })
        
        return chunks
    
    def _process_with_unstructured(self, file_path: str) -> List[Dict[str, Any]]:
        """Process files using unstructured.io"""
        chunks = []
        
        try:
            elements = partition(filename=file_path)
            
            for i, element in enumerate(elements):
                chunks.append({
                    'content': str(element),
                    'metadata': {
                        'file_path': file_path,
                        'file_type': 'document',
                        'element_type': type(element).__name__,
                        'chunk_index': i
                    }
                })
        
        except Exception as e:
            chunks.append({
                'content': f"Error processing with unstructured: {str(e)}",
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'document',
                    'error': True,
                    'chunk_index': 0
                }
            })
        
        return chunks

    def _process_data_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process data files (CSV, JSON, XLSX, etc.)"""
        file_ext = Path(file_path).suffix.lower()
        chunks = []

        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
                return self._process_dataframe(df, file_path, 'csv')

            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return self._process_dataframe(df, file_path, 'excel')

            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                chunks.append({
                    'content': json.dumps(data, indent=2),
                    'metadata': {
                        'file_path': file_path,
                        'file_type': 'data',
                        'format': 'json',
                        'chunk_index': 0
                    }
                })

            elif file_ext in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                chunks.append({
                    'content': yaml.dump(data, default_flow_style=False),
                    'metadata': {
                        'file_path': file_path,
                        'file_type': 'data',
                        'format': 'yaml',
                        'chunk_index': 0
                    }
                })

            elif file_ext == '.xml':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                chunks.append({
                    'content': content,
                    'metadata': {
                        'file_path': file_path,
                        'file_type': 'data',
                        'format': 'xml',
                        'chunk_index': 0
                    }
                })

        except Exception as e:
            chunks.append({
                'content': f"Error processing data file: {str(e)}",
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'data',
                    'error': True,
                    'chunk_index': 0
                }
            })

        return chunks

    def _process_dataframe(self, df: pd.DataFrame, file_path: str, format_type: str) -> List[Dict[str, Any]]:
        """Process pandas DataFrame into chunks"""
        chunks = []

        # Add column information
        column_info = {
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'shape': df.shape
        }

        chunks.append({
            'content': f"Dataset Schema:\nColumns: {', '.join(df.columns)}\nShape: {df.shape}\nData Types:\n" +
                      '\n'.join([f"{col}: {dtype}" for col, dtype in df.dtypes.items()]),
            'metadata': {
                'file_path': file_path,
                'file_type': 'data',
                'format': format_type,
                'chunk_type': 'schema',
                'chunk_index': 0,
                **column_info
            }
        })

        # Chunk data by rows
        chunk_size = 100
        for i in range(0, len(df), chunk_size):
            chunk_df = df.iloc[i:i+chunk_size]

            chunks.append({
                'content': chunk_df.to_string(),
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'data',
                    'format': format_type,
                    'chunk_type': 'data',
                    'chunk_index': len(chunks),
                    'row_start': i,
                    'row_end': min(i + chunk_size, len(df)),
                    **column_info
                }
            })

        return chunks

    def _process_text_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process plain text files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return self._chunk_by_lines(content, file_path, 'text')

    def _process_config_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process configuration files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        file_ext = Path(file_path).suffix.lower()

        return [{
            'content': content,
            'metadata': {
                'file_path': file_path,
                'file_type': 'config',
                'format': file_ext[1:],  # Remove the dot
                'chunk_index': 0
            }
        }]

    def _process_web_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process web files (HTML, CSS, etc.)"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        file_ext = Path(file_path).suffix.lower()

        if file_ext in ['.html', '.htm']:
            # Could parse HTML structure here
            return self._chunk_by_lines(content, file_path, 'html')
        elif file_ext in ['.css', '.scss', '.sass', '.less']:
            return self._process_css_file(content, file_path)
        else:
            return self._chunk_by_lines(content, file_path, 'web')

    def _process_css_file(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Process CSS files by rules"""
        chunks = []
        lines = content.split('\n')
        current_rule = []
        brace_count = 0

        for i, line in enumerate(lines):
            current_rule.append(line)
            brace_count += line.count('{') - line.count('}')

            if brace_count == 0 and current_rule and any('{' in l for l in current_rule):
                chunks.append({
                    'content': '\n'.join(current_rule),
                    'metadata': {
                        'file_path': file_path,
                        'file_type': 'web',
                        'language': 'css',
                        'chunk_index': len(chunks),
                        'start_line': i - len(current_rule) + 1,
                        'end_line': i
                    }
                })
                current_rule = []

        if current_rule:
            chunks.append({
                'content': '\n'.join(current_rule),
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'web',
                    'language': 'css',
                    'chunk_index': len(chunks)
                }
            })

        return chunks

    def _process_sql_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Process SQL files by statements"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Split by semicolons (simple SQL statement separation)
        statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]

        chunks = []
        for i, statement in enumerate(statements):
            chunks.append({
                'content': statement,
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'sql',
                    'statement_type': self._get_sql_statement_type(statement),
                    'chunk_index': i
                }
            })

        return chunks

    def _get_sql_statement_type(self, statement: str) -> str:
        """Determine SQL statement type"""
        statement_upper = statement.upper().strip()

        if statement_upper.startswith('SELECT'):
            return 'SELECT'
        elif statement_upper.startswith('INSERT'):
            return 'INSERT'
        elif statement_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif statement_upper.startswith('DELETE'):
            return 'DELETE'
        elif statement_upper.startswith('CREATE'):
            return 'CREATE'
        elif statement_upper.startswith('ALTER'):
            return 'ALTER'
        elif statement_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'

    def _process_generic_file(self, file_path: str, chunk_strategy: str) -> List[Dict[str, Any]]:
        """Generic file processing fallback"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return self._chunk_by_lines(content, file_path, 'unknown')

        except Exception as e:
            return [{
                'content': f"Error processing file: {str(e)}",
                'metadata': {
                    'file_path': file_path,
                    'file_type': 'unknown',
                    'error': True,
                    'chunk_index': 0
                }
            }]

    def _chunk_by_lines(self, content: str, file_path: str, file_type: str,
                       chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Chunk content by lines with overlap"""
        lines = content.split('\n')
        chunks = []

        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]

            if chunk_lines:
                chunks.append({
                    'content': '\n'.join(chunk_lines),
                    'metadata': {
                        'file_path': file_path,
                        'file_type': file_type,
                        'chunk_index': len(chunks),
                        'start_line': i + 1,
                        'end_line': min(i + chunk_size, len(lines)),
                        'total_lines': len(lines)
                    }
                })

        return chunks
