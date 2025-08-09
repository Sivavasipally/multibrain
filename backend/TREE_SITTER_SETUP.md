# Tree-sitter Code Parsing Setup

This document explains how to set up and use Tree-sitter for advanced code parsing in the RAG Chatbot PWA system.

## Overview

Tree-sitter provides syntax-aware parsing for code files, enabling the system to understand code structure and create more meaningful chunks for RAG operations. The implementation includes:

- **Syntax-aware chunking**: Preserves function and class boundaries
- **Language support**: Python, JavaScript, TypeScript, Java, C/C++, Go, Rust
- **Intelligent fallbacks**: Graceful degradation when parsers are unavailable
- **Cross-platform compatibility**: Works on Linux, macOS, and Windows

## Installation

### Automatic Setup (Recommended)

Use the provided setup script to automatically install Tree-sitter parsers:

```bash
# Install all supported language parsers
python setup_tree_sitter.py

# Install specific languages only
python setup_tree_sitter.py --languages python,javascript,java

# Force reinstallation
python setup_tree_sitter.py --force

# List installed parsers
python setup_tree_sitter.py --list

# Clean all parsers
python setup_tree_sitter.py --clean
```

### Manual Installation

If automatic setup fails, you can manually install parsers:

#### Prerequisites

Ensure you have the required build tools:

```bash
# Ubuntu/Debian
sudo apt install git build-essential

# CentOS/RHEL
sudo yum install git gcc make

# macOS
xcode-select --install
```

#### Manual Parser Installation

```bash
# Create library directory
mkdir -p backend/lib/tree-sitter

# Clone and build a parser (example: Python)
git clone https://github.com/tree-sitter/tree-sitter-python.git
cd tree-sitter-python
make
cp *.so ../backend/lib/tree-sitter/tree-sitter-python.so
```

## Usage

### Automatic Integration

The Tree-sitter service is automatically used by the document processor when processing code files. No additional configuration is required.

```python
from services.document_processor import DocumentProcessor

processor = DocumentProcessor()
chunks = processor.process_file('example.py', 'language-specific')

# Tree-sitter will automatically be used for supported languages
for chunk in chunks:
    if chunk['metadata']['parsing_method'] == 'tree_sitter':
        print(f"Syntax-aware chunk: {chunk['metadata']['chunk_name']}")
```

### Direct Tree-sitter Service Usage

You can also use the Tree-sitter service directly:

```python
from services.tree_sitter_service import tree_sitter_service

# Parse a code file
chunks = tree_sitter_service.parse_code_file('example.py')

# Parse code content directly
code = "def hello():\n    print('world')"
chunks = tree_sitter_service.parse_code(code, 'python')

# Check supported languages
language = tree_sitter_service.detect_language('example.js')
```

## Supported Languages

| Language   | Extension | Parser Status | Fallback Available |
|------------|-----------|---------------|-------------------|
| Python     | .py       | ✅ Full       | ✅ AST-based      |
| JavaScript | .js, .jsx | ✅ Full       | ✅ Regex-based    |
| TypeScript | .ts, .tsx | ✅ Full       | ✅ Regex-based    |
| Java       | .java     | ✅ Full       | ✅ Regex-based    |
| C/C++      | .c, .cpp, .h, .hpp | ✅ Full | ✅ Regex-based |
| Go         | .go       | ✅ Full       | ✅ Regex-based    |
| Rust       | .rs       | ✅ Full       | ✅ Regex-based    |

## Features

### Syntax-Aware Chunking

Tree-sitter parsing provides several advantages over simple text-based chunking:

- **Preserves code boundaries**: Functions and classes are kept intact
- **Understands structure**: Identifies methods, constructors, interfaces
- **Extracts metadata**: Function names, complexity estimates, docstrings
- **Maintains context**: Line numbers and file relationships

### Chunk Metadata

Tree-sitter chunks include rich metadata:

```python
{
    'content': 'def example():\n    """Example function"""\n    pass',
    'metadata': {
        'chunk_type': 'function',
        'chunk_name': 'example',
        'language': 'python',
        'start_line': 1,
        'end_line': 3,
        'parsing_method': 'tree_sitter',
        'syntax_aware': True,
        'has_docstring': True,
        'complexity_estimate': 1,
        'is_callable': True
    }
}
```

### Fallback Mechanisms

The system provides multiple levels of fallback:

1. **Tree-sitter parsing**: Full syntax awareness (preferred)
2. **Regex-based parsing**: Language-specific patterns
3. **AST parsing**: For Python files (legacy support)
4. **Simple chunking**: Line-based splitting (final fallback)

## Configuration

### Environment Variables

```bash
# Optional: Custom library path for Tree-sitter parsers
export TREE_SITTER_LIB_PATH="/custom/path/to/parsers"

# Optional: Enable/disable Tree-sitter (default: auto-detect)
export ENABLE_TREE_SITTER="true"
```

### Performance Tuning

Tree-sitter parsing can be tuned for performance:

```python
# In tree_sitter_service.py, adjust these settings:
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit for parsing
CHUNK_SIZE_LIMIT = 50  # Lines per simple chunk
COMPLEXITY_THRESHOLD = 20  # Max complexity for detailed analysis
```

## Troubleshooting

### Common Issues

#### 1. Parser Compilation Failures

```bash
# Check build dependencies
which gcc make git

# Try manual compilation
cd /path/to/parser/repo
gcc -shared -fPIC -O3 -I src src/parser.c -o parser.so
```

#### 2. Import Errors

```python
# Check if Tree-sitter is available
try:
    import tree_sitter
    print("Tree-sitter available")
except ImportError:
    print("Tree-sitter not available, using fallbacks")
```

#### 3. Parser Loading Issues

```bash
# Check library permissions
ls -la backend/lib/tree-sitter/
chmod 755 backend/lib/tree-sitter/*.so

# Verify parser integrity
file backend/lib/tree-sitter/tree-sitter-python.so
```

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('tree_sitter_service').setLevel(logging.DEBUG)
logging.getLogger('document_processor').setLevel(logging.DEBUG)
```

### Performance Monitoring

Monitor Tree-sitter performance:

```bash
# Check parsing times in logs
grep "Tree-sitter parsing" backend/logs/app.log

# Monitor memory usage during parsing
htop -p $(pgrep python)
```

## Development

### Adding New Language Support

To add support for a new programming language:

1. **Add language configuration** in `tree_sitter_service.py`:

```python
'kotlin': {
    'extensions': ['.kt', '.kts'],
    'lib_name': 'tree-sitter-kotlin',
    'parser': None,
    'fallback_available': True
}
```

2. **Add fallback patterns** for regex-based parsing:

```python
'kotlin': {
    'function': r'(fun\s+\w+.*?\{[\s\S]*?\})',
    'class': r'(class\s+\w+.*?\{[\s\S]*?\})',
    'comment': r'//.*$|/\*[\s\S]*?\*/'
}
```

3. **Update setup script** in `setup_tree_sitter.py`:

```python
'kotlin': {
    'repo': 'https://github.com/fwcd/tree-sitter-kotlin.git',
    'lib_name': 'tree-sitter-kotlin',
    'priority': 'low'
}
```

### Testing

Test Tree-sitter integration:

```python
# Run tests
python -m pytest tests/test_tree_sitter.py

# Test specific language
python -c "
from services.tree_sitter_service import tree_sitter_service
chunks = tree_sitter_service.parse_code('def test(): pass', 'python')
print(f'Found {len(chunks)} chunks')
"
```

## Integration with RAG System

Tree-sitter enhances the RAG system by providing:

- **Better code search**: Function-level granularity for queries
- **Improved context**: Semantic understanding of code structure  
- **Enhanced responses**: More accurate code explanations and examples
- **Intelligent chunking**: Preserves code logic and flow

The integration is transparent to users but provides significantly better results for code-related queries and analysis.