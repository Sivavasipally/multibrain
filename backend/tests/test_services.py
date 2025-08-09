"""
Comprehensive tests for service layer functionality
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, Mock, MagicMock, mock_open
from services.document_processor import DocumentProcessor
from services.vector_service import VectorService
from services.llm_service import LLMService
from services.repository_service import RepositoryService


class TestDocumentProcessor:
    """Test document processing service."""
    
    def test_process_text_file(self):
        """Test processing plain text files."""
        processor = DocumentProcessor()
        
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document.\nIt contains multiple lines.\nFor testing purposes.")
            temp_path = f.name
        
        try:
            result = processor.process_file(temp_path, 'text/plain')
            
            assert 'chunks' in result
            assert 'total_tokens' in result
            assert 'language' in result
            assert len(result['chunks']) > 0
            assert result['total_tokens'] > 0
            assert result['language'] == 'text'
            
            # Verify chunk structure
            chunk = result['chunks'][0]
            assert 'content' in chunk
            assert 'metadata' in chunk
            assert chunk['metadata']['file_path'] == temp_path
            
        finally:
            os.unlink(temp_path)
    
    def test_process_python_file(self):
        """Test processing Python source files."""
        processor = DocumentProcessor()
        
        python_code = '''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return "success"

class TestClass:
    """A test class for demonstration."""
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"

if __name__ == "__main__":
    hello_world()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = f.name
        
        try:
            result = processor.process_file(temp_path, 'text/x-python')
            
            assert result['language'] == 'python'
            assert len(result['chunks']) > 0
            
            # Should extract functions and classes
            content = ''.join(chunk['content'] for chunk in result['chunks'])
            assert 'def hello_world' in content
            assert 'class TestClass' in content
            
        finally:
            os.unlink(temp_path)
    
    def test_process_json_file(self):
        """Test processing JSON files."""
        processor = DocumentProcessor()
        
        json_data = {
            "name": "Test Project",
            "version": "1.0.0",
            "description": "A test project for JSON processing",
            "dependencies": {
                "flask": "2.0.1",
                "requests": "2.25.1"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f, indent=2)
            temp_path = f.name
        
        try:
            result = processor.process_file(temp_path, 'application/json')
            
            assert result['language'] == 'json'
            assert len(result['chunks']) > 0
            
            # Should contain JSON structure information
            content = ''.join(chunk['content'] for chunk in result['chunks'])
            assert 'Test Project' in content
            assert 'dependencies' in content
            
        finally:
            os.unlink(temp_path)
    
    @patch('PyPDF2.PdfReader')
    def test_process_pdf_file(self, mock_pdf_reader):
        """Test processing PDF files."""
        processor = DocumentProcessor()
        
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is extracted text from a PDF document."
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page, mock_page]  # 2 pages
        mock_pdf_reader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            result = processor.process_file(temp_path, 'application/pdf')
            
            assert result['language'] == 'text'
            assert len(result['chunks']) > 0
            
            # Should extract text from all pages
            content = ''.join(chunk['content'] for chunk in result['chunks'])
            assert 'extracted text from a PDF' in content
            
        finally:
            os.unlink(temp_path)
    
    def test_chunk_text_fixed_size(self):
        """Test fixed-size text chunking."""
        processor = DocumentProcessor()
        
        text = "This is a long text that needs to be chunked into smaller pieces. " * 10
        
        chunks = processor.chunk_text(text, strategy='fixed-size', chunk_size=100)
        
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert 'content' in chunk
            assert 'metadata' in chunk
            assert chunk['metadata']['chunk_index'] == i
            assert len(chunk['content']) <= 120  # Allow some overlap
    
    def test_chunk_text_sentence_based(self):
        """Test sentence-based text chunking."""
        processor = DocumentProcessor()
        
        text = "First sentence here. Second sentence follows. Third sentence concludes the paragraph. Fourth sentence starts new thoughts."
        
        chunks = processor.chunk_text(text, strategy='sentence', sentences_per_chunk=2)
        
        assert len(chunks) >= 2
        
        # First chunk should contain first two sentences
        first_chunk = chunks[0]['content']
        assert "First sentence here." in first_chunk
        assert "Second sentence follows." in first_chunk
    
    def test_extract_metadata(self):
        """Test metadata extraction from files."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('# -*- coding: utf-8 -*-\n"""Module docstring."""\nprint("Hello")')
            temp_path = f.name
        
        try:
            metadata = processor.extract_metadata(temp_path)
            
            assert 'file_size' in metadata
            assert 'file_type' in metadata
            assert 'encoding' in metadata
            assert 'language' in metadata
            assert metadata['file_type'] == 'python'
            assert metadata['language'] == 'python'
            
        finally:
            os.unlink(temp_path)
    
    def test_language_detection(self):
        """Test programming language detection."""
        processor = DocumentProcessor()
        
        test_cases = [
            ('test.py', 'def function():\n    pass', 'python'),
            ('test.js', 'function test() { return true; }', 'javascript'),
            ('test.java', 'public class Test { }', 'java'),
            ('test.cpp', '#include <iostream>\nint main() { }', 'cpp'),
            ('test.rs', 'fn main() { println!("Hello"); }', 'rust')
        ]
        
        for filename, content, expected_lang in test_cases:
            detected_lang = processor.detect_language(filename, content)
            assert detected_lang == expected_lang
    
    def test_token_estimation(self):
        """Test token count estimation."""
        processor = DocumentProcessor()
        
        text = "This is a sample text for token counting. It contains multiple words and punctuation!"
        
        token_count = processor.estimate_tokens(text)
        
        assert token_count > 0
        assert token_count < len(text)  # Should be less than character count
        
        # Test with different text sizes
        short_text = "Hello world"
        long_text = "This is a much longer text with many more words and sentences. " * 20
        
        short_tokens = processor.estimate_tokens(short_text)
        long_tokens = processor.estimate_tokens(long_text)
        
        assert long_tokens > short_tokens


class TestVectorService:
    """Test vector service functionality."""
    
    def setUp(self):
        """Set up test vector service."""
        self.vector_service = VectorService()
    
    @patch('faiss.IndexFlatIP')
    def test_create_index(self, mock_faiss_index):
        """Test FAISS index creation."""
        vector_service = VectorService()
        
        # Mock FAISS index
        mock_index = Mock()
        mock_faiss_index.return_value = mock_index
        
        index = vector_service.create_index(dimension=768)
        
        assert index is not None
        mock_faiss_index.assert_called_with(768)
    
    @patch('services.vector_service.VectorService.get_embeddings')
    @patch('faiss.IndexFlatIP')
    def test_add_documents(self, mock_faiss_index, mock_get_embeddings):
        """Test adding documents to vector index."""
        vector_service = VectorService()
        
        # Mock embeddings
        mock_get_embeddings.return_value = [
            [0.1, 0.2, 0.3] * 256,  # 768-dim vector
            [0.4, 0.5, 0.6] * 256
        ]
        
        # Mock FAISS index
        mock_index = Mock()
        mock_faiss_index.return_value = mock_index
        
        documents = [
            {
                'content': 'First document content',
                'metadata': {'id': 1, 'source': 'doc1.txt'}
            },
            {
                'content': 'Second document content',
                'metadata': {'id': 2, 'source': 'doc2.txt'}
            }
        ]
        
        context_id = 1
        result = vector_service.add_documents(documents, context_id)
        
        assert result is True
        mock_get_embeddings.assert_called_once()
        mock_index.add.assert_called_once()
    
    @patch('services.vector_service.VectorService.get_embeddings')
    @patch('faiss.read_index')
    def test_search_documents(self, mock_read_index, mock_get_embeddings):
        """Test searching documents in vector index."""
        vector_service = VectorService()
        
        # Mock query embedding
        mock_get_embeddings.return_value = [[0.2, 0.3, 0.4] * 256]
        
        # Mock FAISS index with search results
        mock_index = Mock()
        mock_index.search.return_value = (
            [[0.95, 0.87, 0.76]],  # Scores
            [[0, 1, 2]]           # Indices
        )
        mock_read_index.return_value = mock_index
        
        # Mock metadata
        with patch('os.path.exists', return_value=True):
            with patch('json.load') as mock_json_load:
                mock_json_load.return_value = {
                    'documents': [
                        {'content': 'First doc', 'metadata': {'source': 'doc1.txt'}},
                        {'content': 'Second doc', 'metadata': {'source': 'doc2.txt'}},
                        {'content': 'Third doc', 'metadata': {'source': 'doc3.txt'}}
                    ]
                }
                
                results = vector_service.search("test query", [1], top_k=3)
                
                assert len(results) == 3
                assert results[0]['score'] == 0.95
                assert results[0]['content'] == 'First doc'
                assert results[1]['score'] == 0.87
    
    def test_delete_context_index(self):
        """Test deleting context vector index."""
        vector_service = VectorService()
        
        with patch('os.path.exists', return_value=True):
            with patch('shutil.rmtree') as mock_rmtree:
                result = vector_service.delete_context(1)
                
                assert result is True
                mock_rmtree.assert_called_once()
    
    @patch('requests.post')
    def test_get_embeddings_gemini(self, mock_post):
        """Test getting embeddings from Gemini API."""
        vector_service = VectorService()
        
        # Mock Gemini API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'embeddings': [
                {'values': [0.1, 0.2, 0.3] * 256},
                {'values': [0.4, 0.5, 0.6] * 256}
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        texts = ['First text', 'Second text']
        embeddings = vector_service.get_embeddings(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 768
        assert embeddings[0][0] == 0.1


class TestLLMService:
    """Test LLM service functionality."""
    
    @patch('requests.post')
    def test_generate_response_success(self, mock_post):
        """Test successful response generation."""
        llm_service = LLMService()
        
        # Mock Gemini API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': 'This is a generated response from the AI model based on the provided context.'
                            }
                        ]
                    }
                }
            ],
            'usageMetadata': {
                'promptTokenCount': 150,
                'candidatesTokenCount': 75,
                'totalTokenCount': 225
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        context_chunks = [
            {
                'content': 'Relevant context information',
                'metadata': {'source': 'doc1.txt'},
                'score': 0.95
            }
        ]
        
        result = llm_service.generate_response(
            query="What is the main topic?",
            context_chunks=context_chunks
        )
        
        assert 'content' in result
        assert 'citations' in result
        assert 'tokens_used' in result
        assert result['tokens_used'] == 225
        assert len(result['citations']) == 1
        assert result['citations'][0]['source'] == 'doc1.txt'
    
    def test_build_prompt(self):
        """Test prompt building for LLM."""
        llm_service = LLMService()
        
        query = "What is machine learning?"
        context_chunks = [
            {
                'content': 'Machine learning is a subset of artificial intelligence.',
                'metadata': {'source': 'ml_intro.txt'},
                'score': 0.98
            },
            {
                'content': 'ML algorithms learn patterns from data.',
                'metadata': {'source': 'algorithms.md'},
                'score': 0.92
            }
        ]
        
        prompt = llm_service.build_prompt(query, context_chunks)
        
        assert query in prompt
        assert 'Machine learning is a subset' in prompt
        assert 'ML algorithms learn patterns' in prompt
        assert 'ml_intro.txt' in prompt
        assert 'algorithms.md' in prompt
    
    def test_extract_citations(self):
        """Test citation extraction from response."""
        llm_service = LLMService()
        
        response_text = "Based on the provided context, machine learning is a subset of AI."
        
        context_chunks = [
            {
                'content': 'Machine learning is a subset of artificial intelligence.',
                'metadata': {'source': 'ml_intro.txt', 'page': 1},
                'score': 0.98
            },
            {
                'content': 'Deep learning is a type of machine learning.',
                'metadata': {'source': 'deep_learning.pdf', 'page': 5},
                'score': 0.85
            }
        ]
        
        citations = llm_service.extract_citations(response_text, context_chunks)
        
        assert len(citations) >= 1
        
        # Should include high-scoring relevant chunks
        high_score_citation = next(c for c in citations if c['score'] == 0.98)
        assert high_score_citation['source'] == 'ml_intro.txt'
        assert 'machine learning' in high_score_citation['content'].lower()
    
    @patch('requests.post')
    def test_streaming_response(self, mock_post):
        """Test streaming response generation."""
        llm_service = LLMService()
        
        # Mock streaming response
        def mock_iter_lines():
            chunks = [
                'data: {"candidates":[{"content":{"parts":[{"text":"This is "}]}}]}',
                'data: {"candidates":[{"content":{"parts":[{"text":"a streaming "}]}}]}',
                'data: {"candidates":[{"content":{"parts":[{"text":"response."}]}}]}',
                'data: [DONE]'
            ]
            for chunk in chunks:
                yield chunk.encode()
        
        mock_response = Mock()
        mock_response.iter_lines.return_value = mock_iter_lines()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        response_generator = llm_service.generate_streaming_response(
            query="Test query",
            context_chunks=[],
            model="gemini-pro"
        )
        
        chunks = list(response_generator)
        
        assert len(chunks) >= 3
        assert any('This is' in chunk.get('content', '') for chunk in chunks)
        assert any('streaming' in chunk.get('content', '') for chunk in chunks)
    
    def test_token_counting(self):
        """Test token counting functionality."""
        llm_service = LLMService()
        
        text = "This is a sample text for token counting estimation."
        
        token_count = llm_service.count_tokens(text)
        
        assert token_count > 0
        assert token_count <= len(text.split())  # Should be reasonable estimate
    
    def test_model_selection(self):
        """Test model selection based on query type."""
        llm_service = LLMService()
        
        # Text-only query should use standard model
        text_model = llm_service.select_model("What is machine learning?", has_images=False)
        assert 'vision' not in text_model.lower()
        
        # Query with images should use vision model
        vision_model = llm_service.select_model("Describe this image", has_images=True)
        assert 'vision' in vision_model.lower() or 'pro' in vision_model.lower()


class TestRepositoryService:
    """Test repository service functionality."""
    
    @patch('subprocess.run')
    def test_clone_repository_success(self, mock_subprocess):
        """Test successful repository cloning."""
        repo_service = RepositoryService()
        
        # Mock successful git clone
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['README.md', 'src', 'tests']):
                result = repo_service.clone_repository(
                    'https://github.com/test/repo.git',
                    branch='main'
                )
                
                assert result['success'] is True
                assert 'local_path' in result
                assert len(result['files']) > 0
    
    @patch('subprocess.run')
    def test_clone_repository_failure(self, mock_subprocess):
        """Test repository cloning failure."""
        repo_service = RepositoryService()
        
        # Mock failed git clone
        mock_subprocess.return_value = Mock(
            returncode=1, 
            stdout="", 
            stderr="Repository not found"
        )
        
        result = repo_service.clone_repository('https://github.com/invalid/repo.git')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_get_repository_info(self):
        """Test getting repository information."""
        repo_service = RepositoryService()
        
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.run') as mock_subprocess:
                # Mock git commands for repo info
                mock_subprocess.side_effect = [
                    Mock(returncode=0, stdout="test-repo\n"),  # repo name
                    Mock(returncode=0, stdout="A test repository\n"),  # description
                    Mock(returncode=0, stdout="main\n"),  # default branch
                    Mock(returncode=0, stdout="100\n")  # commit count
                ]
                
                info = repo_service.get_repository_info('/tmp/test_repo')
                
                assert info['name'] == 'test-repo'
                assert info['description'] == 'A test repository'
                assert info['default_branch'] == 'main'
                assert info['commit_count'] == 100
    
    def test_list_files_with_filters(self):
        """Test listing repository files with extension filters."""
        repo_service = RepositoryService()
        
        # Mock file system
        mock_files = [
            '/repo/README.md',
            '/repo/src/main.py',
            '/repo/src/utils.py',
            '/repo/tests/test_main.py',
            '/repo/docs/api.md',
            '/repo/.gitignore',
            '/repo/package.json'
        ]
        
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/repo', [], ['README.md', '.gitignore', 'package.json']),
                ('/repo/src', [], ['main.py', 'utils.py']),
                ('/repo/tests', [], ['test_main.py']),
                ('/repo/docs', [], ['api.md'])
            ]
            
            # Test with Python files filter
            python_files = repo_service.list_files('/repo', extensions=['py'])
            assert len(python_files) == 3
            assert all(f['path'].endswith('.py') for f in python_files)
            
            # Test with markdown files filter
            md_files = repo_service.list_files('/repo', extensions=['md'])
            assert len(md_files) == 2
            assert all(f['path'].endswith('.md') for f in md_files)
    
    def test_analyze_codebase_structure(self):
        """Test codebase structure analysis."""
        repo_service = RepositoryService()
        
        mock_files = [
            {'path': 'src/main.py', 'type': 'python', 'size': 1024},
            {'path': 'src/utils.py', 'type': 'python', 'size': 512},
            {'path': 'tests/test_main.py', 'type': 'python', 'size': 256},
            {'path': 'README.md', 'type': 'markdown', 'size': 128},
            {'path': 'package.json', 'type': 'json', 'size': 64}
        ]
        
        analysis = repo_service.analyze_codebase_structure(mock_files)
        
        assert 'languages' in analysis
        assert 'total_files' in analysis
        assert 'total_size' in analysis
        assert 'file_types' in analysis
        
        assert analysis['total_files'] == 5
        assert analysis['total_size'] == 1984  # Sum of all file sizes
        assert 'python' in analysis['languages']
        assert analysis['languages']['python'] == 3  # 3 Python files
    
    @patch('subprocess.run')
    def test_get_file_history(self, mock_subprocess):
        """Test getting file change history."""
        repo_service = RepositoryService()
        
        # Mock git log output
        git_log_output = """
commit abc123
Author: John Doe <john@example.com>
Date: 2024-01-15 10:30:00 +0000
Subject: Update main.py with new feature

commit def456
Author: Jane Smith <jane@example.com>
Date: 2024-01-14 15:20:00 +0000
Subject: Fix bug in main.py
"""
        
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout=git_log_output.strip()
        )
        
        with patch('os.path.exists', return_value=True):
            history = repo_service.get_file_history('/repo/src/main.py', limit=10)
            
            assert len(history) == 2
            assert history[0]['commit'] == 'abc123'
            assert history[0]['author'] == 'John Doe'
            assert 'new feature' in history[0]['message']
    
    def test_extract_documentation(self):
        """Test extracting documentation from repository."""
        repo_service = RepositoryService()
        
        mock_files = [
            {'path': 'README.md', 'type': 'markdown'},
            {'path': 'docs/installation.md', 'type': 'markdown'},
            {'path': 'docs/api.md', 'type': 'markdown'},
            {'path': 'CONTRIBUTING.md', 'type': 'markdown'},
            {'path': 'src/main.py', 'type': 'python'}
        ]
        
        with patch('builtins.open', mock_open(read_data="# Documentation\nThis is documentation content.")):
            docs = repo_service.extract_documentation(mock_files)
            
            assert len(docs) == 4  # 4 markdown files
            for doc in docs:
                assert doc['type'] == 'documentation'
                assert 'content' in doc
                assert doc['content'] == "# Documentation\nThis is documentation content."