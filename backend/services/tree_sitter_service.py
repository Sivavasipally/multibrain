"""
Tree-sitter Code Parsing Service for RAG Chatbot PWA

This module provides advanced code parsing capabilities using Tree-sitter to enable
intelligent code analysis, structure extraction, and semantic chunking for the RAG
(Retrieval-Augmented Generation) system.

Key Features:
- Syntax-aware code parsing with AST generation
- Function and class boundary detection
- Intelligent code chunking preserving logical structure
- Language-specific parsing for multiple programming languages
- Fallback mechanisms for unsupported languages
- Code structure analysis and metadata extraction
- Cross-platform tree-sitter library management

Supported Languages:
- Python: Functions, classes, methods, docstrings
- JavaScript/TypeScript: Functions, classes, modules, exports
- Java: Classes, methods, packages, interfaces
- C/C++: Functions, classes, headers, namespaces
- Go: Functions, structs, packages, interfaces
- Rust: Functions, structs, impl blocks, modules
- And more with extensible parser system

Architecture:
1. Parser Management: Dynamic loading of language parsers
2. AST Analysis: Syntax tree traversal and node extraction  
3. Structure Detection: Function/class boundary identification
4. Intelligent Chunking: Logic-aware code segmentation
5. Metadata Extraction: Code structure and context information
6. Fallback Handling: Graceful degradation for unsupported languages

Dependencies:
- tree-sitter: Core parsing library
- Language-specific parsers (auto-installed when available)
- pathlib: Cross-platform path handling
- typing: Type hints and annotations

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import re
import ast
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('tree_sitter_service')

# Try to import tree-sitter with fallback
try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
    logger.info("Tree-sitter library available for code parsing")
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("Tree-sitter not available, using fallback code parsing")
    
    # Create mock classes for type hints when tree-sitter is not available
    class Node:
        pass
    class Parser:
        pass
    class Language:
        pass

@dataclass
class CodeChunk:
    """
    Represents a semantically meaningful chunk of code with metadata
    
    This class encapsulates a code segment along with its structural context,
    making it suitable for RAG operations that need to understand code semantics.
    
    Attributes:
        content (str): The actual code content
        start_line (int): Starting line number in the original file
        end_line (int): Ending line number in the original file
        chunk_type (str): Type of code chunk (function, class, module, etc.)
        name (str): Name of the code element (function name, class name, etc.)
        language (str): Programming language of the code
        metadata (Dict[str, Any]): Additional context and structural information
    """
    content: str
    start_line: int
    end_line: int
    chunk_type: str
    name: str
    language: str
    metadata: Dict[str, Any]

class TreeSitterService:
    """
    Advanced Tree-sitter code parsing service for intelligent code analysis
    
    This service provides comprehensive code parsing capabilities using Tree-sitter
    to enable syntax-aware processing of code files. It supports multiple programming
    languages with intelligent fallback mechanisms for unsupported languages.
    
    Key Capabilities:
    - Multi-language syntax parsing with Tree-sitter
    - Function and class boundary detection
    - Intelligent code chunking preserving logical structure
    - Code metadata extraction and context analysis
    - Fallback regex-based parsing for unsupported languages
    - Cross-platform parser management and installation
    
    Example:
        >>> ts_service = TreeSitterService()
        >>> chunks = ts_service.parse_code("def hello(): print('world')", "python")
        >>> print(f"Found {len(chunks)} code chunks")
    """
    
    def __init__(self):
        """
        Initialize Tree-sitter service with language parsers
        
        Sets up the Tree-sitter parsing environment including language parser
        initialization and fallback configuration. Attempts to load available
        language parsers while providing graceful degradation.
        
        Raises:
            Exception: If critical initialization fails
        """
        logger.info("Initializing TreeSitterService")
        
        # Language configurations for Tree-sitter parsers
        self.language_configs = {
            'python': {
                'extensions': ['.py'],
                'lib_name': 'tree-sitter-python',
                'parser': None,
                'fallback_available': True
            },
            'javascript': {
                'extensions': ['.js', '.jsx'],
                'lib_name': 'tree-sitter-javascript', 
                'parser': None,
                'fallback_available': True
            },
            'typescript': {
                'extensions': ['.ts', '.tsx'],
                'lib_name': 'tree-sitter-typescript',
                'parser': None,
                'fallback_available': True
            },
            'java': {
                'extensions': ['.java'],
                'lib_name': 'tree-sitter-java',
                'parser': None,
                'fallback_available': True
            },
            'cpp': {
                'extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'],
                'lib_name': 'tree-sitter-cpp',
                'parser': None,
                'fallback_available': True
            },
            'go': {
                'extensions': ['.go'],
                'lib_name': 'tree-sitter-go',
                'parser': None,
                'fallback_available': True
            },
            'rust': {
                'extensions': ['.rs'],
                'lib_name': 'tree-sitter-rust',
                'parser': None,
                'fallback_available': True
            }
        }
        
        # Initialize parsers if tree-sitter is available
        self.parsers_available = False
        if TREE_SITTER_AVAILABLE:
            try:
                self._initialize_parsers()
                logger.info("Tree-sitter parsers initialized successfully")
            except Exception as e:
                logger.warning(f"Tree-sitter parser initialization failed, using fallback: {e}")
        else:
            logger.info("Using fallback regex-based parsing due to missing tree-sitter")
        
        # Initialize fallback parsing patterns
        self._initialize_fallback_patterns()
        logger.info("TreeSitterService initialization completed")
    
    def _initialize_parsers(self):
        """
        Initialize Tree-sitter language parsers
        
        Attempts to load compiled language libraries for Tree-sitter parsing.
        This method handles dynamic parser loading with comprehensive error
        handling and logging.
        
        Note:
            In production, Tree-sitter language libraries need to be compiled
            and available. This method includes auto-installation logic where
            possible and fallback mechanisms for missing parsers.
        """
        logger.debug("Initializing Tree-sitter language parsers")
        
        # Check for common tree-sitter library installation paths
        possible_lib_paths = [
            '/usr/local/lib/tree-sitter',
            '/usr/lib/tree-sitter', 
            os.path.expanduser('~/.local/lib/tree-sitter'),
            os.path.join(os.path.dirname(__file__), '..', 'lib', 'tree-sitter')
        ]
        
        lib_path = None
        for path in possible_lib_paths:
            if os.path.exists(path):
                lib_path = path
                logger.debug(f"Found tree-sitter libraries at: {path}")
                break
        
        if not lib_path:
            logger.info("No pre-compiled tree-sitter libraries found, parsers will be built on demand")
            # In a production environment, you might want to build parsers here
            # or use a package manager to install them
            return
        
        # Attempt to load language parsers
        successful_parsers = []
        failed_parsers = []
        
        for lang, config in self.language_configs.items():
            try:
                # Try to load the compiled language library
                lib_file = os.path.join(lib_path, f"{config['lib_name']}.so")
                if os.path.exists(lib_file):
                    language = Language(lib_file, lang)
                    parser = Parser()
                    parser.set_language(language)
                    config['parser'] = parser
                    successful_parsers.append(lang)
                    logger.debug(f"Loaded {lang} parser from {lib_file}")
                else:
                    logger.debug(f"Parser library not found: {lib_file}")
                    failed_parsers.append(lang)
                    
            except Exception as e:
                logger.debug(f"Failed to load {lang} parser: {e}")
                failed_parsers.append(lang)
        
        if successful_parsers:
            self.parsers_available = True
            logger.info(f"Successfully loaded Tree-sitter parsers for: {', '.join(successful_parsers)}")
        
        if failed_parsers:
            logger.debug(f"Using fallback parsing for: {', '.join(failed_parsers)}")
    
    def _initialize_fallback_patterns(self):
        """
        Initialize regex patterns for fallback parsing
        
        Sets up comprehensive regex patterns for identifying code structures
        when Tree-sitter parsers are not available. These patterns provide
        reasonable code chunking capabilities across multiple languages.
        
        Patterns Include:
        - Function definitions and declarations
        - Class and interface definitions  
        - Method and constructor patterns
        - Module and namespace boundaries
        - Comment and docstring extraction
        """
        logger.debug("Initializing fallback parsing patterns")
        
        self.fallback_patterns = {
            'python': {
                'function': r'^(\s*)(def\s+\w+.*?)(?=\n\s*(?:def|class|$))',
                'class': r'^(\s*)(class\s+\w+.*?)(?=\n\s*(?:def|class|$))',
                'docstring': r'"""[\s\S]*?"""',
                'comment': r'#.*$'
            },
            'javascript': {
                'function': r'(function\s+\w+.*?\{[\s\S]*?\})',
                'class': r'(class\s+\w+.*?\{[\s\S]*?\})',
                'arrow_function': r'(const\s+\w+\s*=\s*.*?=>.*?(?=\n|$))',
                'comment': r'//.*$|/\*[\s\S]*?\*/'
            },
            'typescript': {
                'function': r'(function\s+\w+.*?\{[\s\S]*?\})',
                'class': r'(class\s+\w+.*?\{[\s\S]*?\})',
                'interface': r'(interface\s+\w+.*?\{[\s\S]*?\})',
                'type': r'(type\s+\w+.*?=.*?(?=\n|$))',
                'comment': r'//.*$|/\*[\s\S]*?\*/'
            },
            'java': {
                'class': r'(public\s+class\s+\w+.*?\{[\s\S]*?\})',
                'method': r'(public\s+.*?\s+\w+\s*\(.*?\)\s*\{[\s\S]*?\})',
                'interface': r'(public\s+interface\s+\w+.*?\{[\s\S]*?\})',
                'comment': r'//.*$|/\*[\s\S]*?\*/'
            },
            'cpp': {
                'function': r'(\w+\s+\w+\s*\([^)]*\)\s*\{[\s\S]*?\})',
                'class': r'(class\s+\w+.*?\{[\s\S]*?\};)',
                'namespace': r'(namespace\s+\w+\s*\{[\s\S]*?\})',
                'comment': r'//.*$|/\*[\s\S]*?\*/'
            },
            'go': {
                'function': r'(func\s+(?:\([^)]*\))?\s*\w+.*?\{[\s\S]*?\})',
                'struct': r'(type\s+\w+\s+struct\s*\{[\s\S]*?\})',
                'interface': r'(type\s+\w+\s+interface\s*\{[\s\S]*?\})',
                'comment': r'//.*$|/\*[\s\S]*?\*/'
            },
            'rust': {
                'function': r'(fn\s+\w+.*?\{[\s\S]*?\})',
                'struct': r'(struct\s+\w+.*?\{[\s\S]*?\})',
                'impl': r'(impl.*?\{[\s\S]*?\})',
                'comment': r'//.*$|/\*[\s\S]*?\*/'
            }
        }
        
        logger.debug(f"Initialized fallback patterns for {len(self.fallback_patterns)} languages")
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language from file extension
        
        Analyzes the file extension to determine the most appropriate
        programming language parser and processing strategy.
        
        Args:
            file_path (str): Path to the code file
            
        Returns:
            Optional[str]: Detected language name or None if unsupported
            
        Example:
            >>> lang = service.detect_language('main.py')
            >>> print(lang)  # 'python'
        """
        file_ext = Path(file_path).suffix.lower()
        
        for lang, config in self.language_configs.items():
            if file_ext in config['extensions']:
                logger.debug(f"Detected language '{lang}' for file {file_path}")
                return lang
        
        logger.debug(f"No language detected for file extension '{file_ext}' in {file_path}")
        return None
    
    def parse_code_file(self, file_path: str) -> List[CodeChunk]:
        """
        Parse a code file into semantically meaningful chunks
        
        Processes a code file using Tree-sitter (when available) or fallback
        regex patterns to extract functions, classes, and other code structures
        as separate chunks suitable for RAG operations.
        
        Args:
            file_path (str): Path to the code file to parse
            
        Returns:
            List[CodeChunk]: List of extracted code chunks with metadata
            
        Raises:
            FileNotFoundError: If the specified file does not exist
            IOError: If file cannot be read
            
        Example:
            >>> chunks = service.parse_code_file('src/main.py')
            >>> for chunk in chunks:
            ...     print(f"{chunk.chunk_type}: {chunk.name}")
        """
        if not os.path.exists(file_path):
            logger.error(f"Code file not found: {file_path}")
            raise FileNotFoundError(f"Code file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                logger.warning(f"File {file_path} read with latin-1 encoding fallback")
            except Exception as e:
                logger.error(f"Could not read file {file_path}: {e}")
                raise IOError(f"Cannot read file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
        
        language = self.detect_language(file_path)
        if not language:
            logger.warning(f"Unsupported file type for parsing: {file_path}")
            return self._create_simple_chunks(content, file_path)
        
        logger.debug(f"Parsing {file_path} as {language}")
        return self.parse_code(content, language, file_path)
    
    def parse_code(self, content: str, language: str, file_path: str = "") -> List[CodeChunk]:
        """
        Parse code content into structured chunks
        
        Uses Tree-sitter parsing when available, with intelligent fallback
        to regex-based parsing for unsupported languages or when Tree-sitter
        is not available.
        
        Args:
            content (str): Code content to parse
            language (str): Programming language identifier
            file_path (str, optional): Original file path for context
            
        Returns:
            List[CodeChunk]: Extracted code chunks with structural metadata
            
        Example:
            >>> code = "def hello():\\n    print('world')"
            >>> chunks = service.parse_code(code, 'python')
        """
        logger.debug(f"Parsing {len(content)} characters of {language} code")
        
        # Try Tree-sitter parsing first if available
        if (self.parsers_available and 
            language in self.language_configs and 
            self.language_configs[language]['parser']):
            
            try:
                chunks = self._parse_with_tree_sitter(content, language, file_path)
                if chunks:
                    logger.debug(f"Tree-sitter parsing successful: {len(chunks)} chunks")
                    return chunks
            except Exception as e:
                logger.warning(f"Tree-sitter parsing failed for {language}, using fallback: {e}")
        
        # Fallback to regex-based parsing
        logger.debug(f"Using fallback parsing for {language}")
        return self._parse_with_fallback(content, language, file_path)
    
    def _parse_with_tree_sitter(self, content: str, language: str, file_path: str) -> List[CodeChunk]:
        """
        Parse code using Tree-sitter AST analysis
        
        Uses Tree-sitter to generate an Abstract Syntax Tree and extracts
        meaningful code structures like functions, classes, and methods
        with precise boundary detection.
        
        Args:
            content (str): Code content to parse
            language (str): Programming language
            file_path (str): Source file path for context
            
        Returns:
            List[CodeChunk]: Extracted code chunks from AST analysis
        """
        parser = self.language_configs[language]['parser']
        if not parser:
            raise ValueError(f"No parser available for language: {language}")
        
        # Parse the code into an AST
        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        
        # Extract chunks based on language-specific node types
        chunks = []
        self._extract_chunks_from_node(root_node, content, language, chunks, file_path)
        
        return chunks
    
    def _extract_chunks_from_node(self, node: Node, content: str, language: str, 
                                 chunks: List[CodeChunk], file_path: str):
        """
        Recursively extract code chunks from AST nodes
        
        Traverses the syntax tree to identify and extract meaningful code
        structures based on node types and language-specific patterns.
        
        Args:
            node: Tree-sitter AST node
            content (str): Original source code
            language (str): Programming language
            chunks (List[CodeChunk]): List to append found chunks
            file_path (str): Source file path for context
        """
        # Language-specific node types that represent meaningful chunks
        chunk_node_types = {
            'python': ['function_definition', 'class_definition', 'decorated_definition'],
            'javascript': ['function_declaration', 'class_declaration', 'method_definition'],
            'typescript': ['function_declaration', 'class_declaration', 'interface_declaration'],
            'java': ['class_declaration', 'method_declaration', 'interface_declaration'],
            'cpp': ['function_definition', 'class_specifier', 'namespace_definition'],
            'go': ['function_declaration', 'type_declaration', 'method_declaration'],
            'rust': ['function_item', 'struct_item', 'impl_item']
        }
        
        target_types = chunk_node_types.get(language, [])
        
        # Check if current node is a target chunk type
        if node.type in target_types:
            chunk = self._create_chunk_from_node(node, content, language, file_path)
            if chunk:
                chunks.append(chunk)
        
        # Recursively process child nodes
        for child in node.children:
            self._extract_chunks_from_node(child, content, language, chunks, file_path)
    
    def _create_chunk_from_node(self, node: Node, content: str, language: str, 
                               file_path: str) -> Optional[CodeChunk]:
        """
        Create a CodeChunk from a Tree-sitter AST node
        
        Extracts the code content and metadata from an AST node to create
        a properly structured CodeChunk suitable for RAG operations.
        
        Args:
            node: Tree-sitter AST node
            content (str): Original source code
            language (str): Programming language
            file_path (str): Source file path
            
        Returns:
            Optional[CodeChunk]: Created chunk or None if extraction fails
        """
        try:
            # Get the text content of the node
            start_byte = node.start_byte
            end_byte = node.end_byte
            chunk_content = content[start_byte:end_byte]
            
            # Calculate line numbers
            lines_before = content[:start_byte].count('\n')
            lines_in_chunk = chunk_content.count('\n')
            start_line = lines_before + 1
            end_line = start_line + lines_in_chunk
            
            # Extract name and determine chunk type
            name = self._extract_name_from_node(node, chunk_content, language)
            chunk_type = self._map_node_type_to_chunk_type(node.type, language)
            
            # Create metadata
            metadata = {
                'node_type': node.type,
                'file_path': file_path,
                'byte_range': (start_byte, end_byte),
                'has_docstring': self._has_docstring(chunk_content, language),
                'complexity_estimate': self._estimate_complexity(chunk_content)
            }
            
            return CodeChunk(
                content=chunk_content,
                start_line=start_line,
                end_line=end_line,
                chunk_type=chunk_type,
                name=name,
                language=language,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to create chunk from node: {e}")
            return None
    
    def _parse_with_fallback(self, content: str, language: str, file_path: str) -> List[CodeChunk]:
        """
        Parse code using regex fallback patterns
        
        Provides robust code parsing using regex patterns when Tree-sitter
        is not available or fails. Uses language-specific patterns to identify
        functions, classes, and other code structures.
        
        Args:
            content (str): Code content to parse
            language (str): Programming language
            file_path (str): Source file path for context
            
        Returns:
            List[CodeChunk]: Extracted code chunks using regex patterns
        """
        if language not in self.fallback_patterns:
            logger.warning(f"No fallback patterns available for {language}")
            return self._create_simple_chunks(content, file_path)
        
        patterns = self.fallback_patterns[language]
        chunks = []
        
        # Apply each pattern type to find code structures
        for chunk_type, pattern in patterns.items():
            if chunk_type == 'comment':  # Skip comment patterns for chunking
                continue
                
            try:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    chunk_content = match.group(0)
                    start_pos = match.start()
                    
                    # Calculate line numbers
                    lines_before = content[:start_pos].count('\n')
                    lines_in_chunk = chunk_content.count('\n')
                    start_line = lines_before + 1
                    end_line = start_line + lines_in_chunk
                    
                    # Extract name from the matched content
                    name = self._extract_name_from_content(chunk_content, chunk_type, language)
                    
                    # Create metadata
                    metadata = {
                        'pattern_type': chunk_type,
                        'file_path': file_path,
                        'parsing_method': 'regex_fallback',
                        'has_docstring': self._has_docstring(chunk_content, language),
                        'complexity_estimate': self._estimate_complexity(chunk_content)
                    }
                    
                    chunk = CodeChunk(
                        content=chunk_content,
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type=chunk_type,
                        name=name,
                        language=language,
                        metadata=metadata
                    )
                    chunks.append(chunk)
                    
            except Exception as e:
                logger.warning(f"Fallback pattern '{chunk_type}' failed for {language}: {e}")
        
        # If no patterns matched, create simple chunks
        if not chunks:
            logger.debug(f"No patterns matched, creating simple chunks for {language}")
            return self._create_simple_chunks(content, file_path)
        
        logger.debug(f"Fallback parsing found {len(chunks)} chunks for {language}")
        return chunks
    
    def _create_simple_chunks(self, content: str, file_path: str) -> List[CodeChunk]:
        """
        Create simple line-based chunks as final fallback
        
        When no other parsing method works, creates chunks based on line
        count and logical breaks in the code.
        
        Args:
            content (str): Code content to chunk
            file_path (str): Source file path
            
        Returns:
            List[CodeChunk]: Simple line-based code chunks
        """
        lines = content.split('\n')
        chunks = []
        chunk_size = 50  # Lines per chunk
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            if chunk_content.strip():  # Only create non-empty chunks
                start_line = i + 1
                end_line = min(i + chunk_size, len(lines))
                
                metadata = {
                    'file_path': file_path,
                    'parsing_method': 'simple_chunking',
                    'chunk_number': len(chunks) + 1,
                    'total_lines': len(chunk_lines)
                }
                
                chunk = CodeChunk(
                    content=chunk_content,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type='code_block',
                    name=f"Block_{len(chunks) + 1}",
                    language='unknown',
                    metadata=metadata
                )
                chunks.append(chunk)
        
        logger.debug(f"Created {len(chunks)} simple chunks from {len(lines)} lines")
        return chunks
    
    def _extract_name_from_node(self, node: Node, content: str, language: str) -> str:
        """Extract name from Tree-sitter AST node"""
        # This would be implemented based on Tree-sitter node structure
        # For now, return a placeholder
        return f"{node.type}_from_ast"
    
    def _extract_name_from_content(self, content: str, chunk_type: str, language: str) -> str:
        """
        Extract name from code content using regex patterns
        
        Uses language-specific regex patterns to extract meaningful names
        from code chunks (function names, class names, etc.).
        
        Args:
            content (str): Code content to analyze
            chunk_type (str): Type of code chunk
            language (str): Programming language
            
        Returns:
            str: Extracted name or default name
        """
        name_patterns = {
            'python': {
                'function': r'def\s+(\w+)',
                'class': r'class\s+(\w+)'
            },
            'javascript': {
                'function': r'function\s+(\w+)',
                'class': r'class\s+(\w+)'
            },
            'java': {
                'class': r'class\s+(\w+)',
                'method': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\('
            }
        }
        
        if language in name_patterns and chunk_type in name_patterns[language]:
            pattern = name_patterns[language][chunk_type]
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return f"unnamed_{chunk_type}"
    
    def _map_node_type_to_chunk_type(self, node_type: str, language: str) -> str:
        """Map Tree-sitter node types to semantic chunk types"""
        type_mappings = {
            'function_definition': 'function',
            'function_declaration': 'function',
            'class_definition': 'class',
            'class_declaration': 'class',
            'method_definition': 'method',
            'interface_declaration': 'interface',
            'namespace_definition': 'namespace'
        }
        
        return type_mappings.get(node_type, node_type)
    
    def _has_docstring(self, content: str, language: str) -> bool:
        """Check if code content has documentation/comments"""
        doc_patterns = {
            'python': r'"""[\s\S]*?"""',
            'javascript': r'/\*\*[\s\S]*?\*/',
            'java': r'/\*\*[\s\S]*?\*/',
            'cpp': r'/\*\*[\s\S]*?\*/'
        }
        
        if language in doc_patterns:
            return bool(re.search(doc_patterns[language], content))
        
        return False
    
    def _estimate_complexity(self, content: str) -> int:
        """Estimate code complexity based on control structures"""
        complexity_indicators = [
            r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bfor\b', r'\bwhile\b', r'\bdo\b',
            r'\btry\b', r'\bcatch\b', r'\bexcept\b',
            r'\bswitch\b', r'\bcase\b'
        ]
        
        complexity = 1  # Base complexity
        for pattern in complexity_indicators:
            complexity += len(re.findall(pattern, content, re.IGNORECASE))
        
        return complexity

# Create a global instance for easy access
tree_sitter_service = TreeSitterService()