"""
Vector Storage Service using FAISS for RAG (Retrieval-Augmented Generation)

This module provides comprehensive vector storage and similarity search capabilities
for the RAG Chatbot PWA. It supports multiple embedding models and provides fallback
mechanisms for robust operation across different environments.

Key Features:
- FAISS-based vector indexing for fast similarity search
- Multiple embedding model support (Gemini, Sentence Transformers, fallback)
- Automatic fallback mechanisms for missing dependencies
- Batch processing for efficient vector operations
- Comprehensive error handling and logging
- Support for both file-based and in-memory vector stores

Supported Embedding Models:
- Google Gemini text-embedding-004 (primary)
- Sentence Transformers all-MiniLM-L6-v2 (fallback)
- Basic TF-IDF vectorization (emergency fallback)

Dependencies:
- faiss-cpu: Fast similarity search library
- sentence-transformers: Local embedding model
- google-generativeai: Gemini API for embeddings
- numpy: Numerical operations

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import json
import pickle
import time
import numpy as np
from typing import List, Dict, Any, Optional

# Import logging functionality
from logging_config import get_logger, log_error_with_context
from services.detailed_logger import (
    detailed_logger, log_vector_operation, log_chunk_processing,
    VectorOperationLog, ChunkMetadata, track_operation
)

# Initialize logger
logger = get_logger('vector_service')

# Optional imports with fallbacks
try:
    import faiss
    FAISS_AVAILABLE = True
    logger.info("FAISS library loaded successfully")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Vector search will be limited to basic similarity search.")

# Check if sentence transformers is available without importing
try:
    import importlib.util
    spec = importlib.util.find_spec("sentence_transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = spec is not None
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.info("Sentence Transformers available for local embeddings")
    else:
        logger.warning("Sentence Transformers not available. Will use alternative embedding methods.")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("Failed to check Sentence Transformers availability")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("Google Generative AI library loaded successfully")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available. Gemini embeddings will be unavailable.")

class VectorService:
    """
    Comprehensive vector storage and similarity search service for RAG systems
    
    This class provides a robust vector database implementation using FAISS for 
    fast similarity search operations. It supports multiple embedding models with
    automatic fallback mechanisms and comprehensive error handling.
    
    Key Features:
    - Multi-model embedding support (Gemini, Sentence Transformers, fallback)
    - FAISS-based vector indexing with cosine similarity search
    - Automatic fallback to simple vector operations when FAISS unavailable
    - Batch processing for efficient operations
    - Comprehensive error handling and logging
    - Support for both persistent and in-memory vector stores
    
    Architecture:
    1. Embedding Creation: Text → Vector embeddings using selected model
    2. Vector Storage: FAISS index creation with metadata persistence
    3. Similarity Search: Query embedding → Similar document retrieval
    4. Result Ranking: Cosine similarity scoring and ranking
    
    Attributes:
        embedding_model (str): Primary embedding model identifier
        sentence_transformer: Local Sentence Transformers model instance
        gemini_client: Google Gemini API client for embeddings
        
    Example:
        >>> service = VectorService('text-embedding-004')
        >>> chunks = [{'content': 'Example text', 'source': 'doc1.pdf'}]
        >>> service.create_vector_store(chunks, '/path/to/store')
        >>> results = service.search_similar('/path/to/store', 'query text', top_k=5)
    """
    
    def __init__(self, embedding_model: str = 'text-embedding-004'):
        """
        Initialize the Vector Service with specified embedding model
        
        Args:
            embedding_model (str): Embedding model to use. Options:
                - 'text-embedding-004': Google Gemini embeddings (default)
                - 'all-MiniLM-L6-v2': Sentence Transformers local model
                - 'fallback': Basic TF-IDF vectorization
                
        Raises:
            ValueError: If embedding_model is not supported
            ImportError: If required dependencies are missing
        """
        logger.info(f"Initializing VectorService with embedding model: {embedding_model}")
        
        self.embedding_model = embedding_model
        self.sentence_transformer = None
        self.gemini_client = None
        
        # Validate embedding model
        supported_models = ['text-embedding-004', 'all-MiniLM-L6-v2', 'fallback']
        if embedding_model not in supported_models:
            logger.warning(f"Unknown embedding model: {embedding_model}. Supported: {supported_models}")
        
        # Initialize embedding models
        try:
            self._init_embedding_models()
            logger.info("VectorService initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}")
            log_error_with_context(e, {"embedding_model": embedding_model})
            raise
    
    def _init_embedding_models(self):
        """
        Initialize embedding models based on availability and configuration
        
        This method attempts to initialize multiple embedding models in order of preference:
        1. Google Gemini text-embedding-004 (if API key available)
        2. Sentence Transformers all-MiniLM-L6-v2 (local processing)
        3. Fallback to basic TF-IDF if neither available
        
        The initialization is fault-tolerant and will use the best available option.
        
        Raises:
            Exception: If no embedding models can be initialized
        """
        logger.debug("Starting embedding models initialization")
        initialized_models = []
        
        try:
            # Initialize Sentence Transformers for local embeddings
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    logger.debug("Initializing Sentence Transformers model")
                    from sentence_transformers import SentenceTransformer
                    self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                    initialized_models.append("Sentence Transformers")
                    logger.info("Sentence Transformers model initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Sentence Transformers: {e}")
                    self.sentence_transformer = None
            else:
                logger.debug("Sentence Transformers not available, skipping initialization")

            # Initialize Gemini for text-embedding-004
            if self.embedding_model == 'text-embedding-004' and GEMINI_AVAILABLE:
                logger.debug("Initializing Gemini embeddings client")
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    try:
                        genai.configure(api_key=api_key)
                        self.gemini_client = genai
                        initialized_models.append("Gemini text-embedding-004")
                        logger.info("Gemini embeddings client initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to configure Gemini client: {e}")
                        self.gemini_client = None
                else:
                    logger.warning("GEMINI_API_KEY not found in environment variables")
                    logger.info("Set GEMINI_API_KEY to enable Gemini embeddings")
            elif not GEMINI_AVAILABLE:
                logger.debug("Google Generative AI not available, skipping Gemini initialization")

            # Log initialization results
            if initialized_models:
                logger.info(f"Successfully initialized embedding models: {', '.join(initialized_models)}")
            else:
                logger.warning("No embedding models could be initialized - will use fallback methods")
                
        except Exception as e:
            logger.error(f"Critical error during embedding models initialization: {e}")
            log_error_with_context(e, {"embedding_model": self.embedding_model})
            raise Exception(f"Failed to initialize any embedding models: {e}")
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts"""
        if self.embedding_model == 'text-embedding-004' and self.gemini_client:
            return self._create_gemini_embeddings(texts)
        else:
            return self._create_sentence_transformer_embeddings(texts)
    
    def _create_gemini_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings using Gemini text-embedding-004"""
        embeddings = []
        
        for text in texts:
            try:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            except Exception as e:
                print(f"Error creating Gemini embedding: {e}")
                # Fallback to sentence transformer
                fallback_embedding = self.sentence_transformer.encode([text])[0]
                embeddings.append(fallback_embedding.tolist())
        
        return np.array(embeddings, dtype=np.float32)
    
    def _create_sentence_transformer_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings using Sentence Transformers"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not self.sentence_transformer:
            # Fallback to simple embeddings
            print("Warning: Using fallback embeddings (not recommended for production)")
            return self._create_fallback_embeddings(texts)

        embeddings = self.sentence_transformer.encode(texts)
        return np.array(embeddings, dtype=np.float32)

    def _create_fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create simple fallback embeddings when proper models aren't available"""
        # Very basic embedding using character frequencies (not recommended for production)
        embeddings = []
        for text in texts:
            # Create a simple 384-dimensional vector based on text characteristics
            embedding = np.zeros(384)
            if text:
                # Use text length, character frequencies, etc.
                embedding[0] = len(text) / 1000.0  # Normalized length
                for i, char in enumerate(text[:100]):  # First 100 chars
                    embedding[i % 384] += ord(char) / 1000.0
            embeddings.append(embedding)

        return np.array(embeddings, dtype=np.float32)
    
    def create_vector_store(self, chunks: List[Dict[str, Any]], store_path: str) -> str:
        """Create a FAISS vector store from document chunks"""
        if not chunks:
            raise ValueError("No chunks provided")

        if not FAISS_AVAILABLE:
            print("Warning: FAISS not available. Creating simple vector store.")
            return self._create_simple_vector_store(chunks, store_path)

        # Extract text content
        texts = [chunk['content'] for chunk in chunks]

        # Create embeddings
        embeddings = self.create_embeddings(texts)

        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add embeddings to index
        index.add(embeddings)
        
        # Create store directory
        os.makedirs(store_path, exist_ok=True)
        
        # Save FAISS index
        index_path = os.path.join(store_path, 'index.faiss')
        faiss.write_index(index, index_path)
        
        # Save metadata
        metadata = {
            'chunks': chunks,
            'embedding_model': self.embedding_model,
            'dimension': dimension,
            'total_chunks': len(chunks)
        }
        
        metadata_path = os.path.join(store_path, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Save embeddings for debugging
        embeddings_path = os.path.join(store_path, 'embeddings.npy')
        np.save(embeddings_path, embeddings)
        
        return store_path

    def _create_simple_vector_store(self, chunks: List[Dict[str, Any]], store_path: str) -> str:
        """Create a simple vector store without FAISS"""
        # Extract text content
        texts = [chunk['content'] for chunk in chunks]

        # Create embeddings
        embeddings = self.create_embeddings(texts)

        # Create store directory
        os.makedirs(store_path, exist_ok=True)

        # Save metadata
        metadata = {
            'chunks': chunks,
            'embedding_model': self.embedding_model,
            'dimension': embeddings.shape[1],
            'total_chunks': len(chunks),
            'store_type': 'simple'  # Mark as simple store
        }

        metadata_path = os.path.join(store_path, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Save embeddings
        embeddings_path = os.path.join(store_path, 'embeddings.npy')
        np.save(embeddings_path, embeddings)

        return store_path

    def load_vector_store(self, store_path: str) -> tuple:
        """Load vector store and metadata (FAISS or simple)"""
        # Handle both directory paths and file paths
        # If store_path ends with index.faiss, get the parent directory
        if store_path.endswith('index.faiss') or store_path.endswith('index.faiss\\') or store_path.endswith('index.faiss/'):
            store_dir = os.path.dirname(store_path)
        else:
            store_dir = store_path
            
        metadata_path = os.path.join(store_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Vector store metadata not found at {store_dir} (derived from {store_path})")

        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Check store type
        store_type = metadata.get('store_type', 'faiss')

        if store_type == 'simple' or not FAISS_AVAILABLE:
            # Load simple store (just embeddings)
            embeddings_path = os.path.join(store_dir, 'embeddings.npy')
            if os.path.exists(embeddings_path):
                embeddings = np.load(embeddings_path)
                return embeddings, metadata
            else:
                raise FileNotFoundError(f"Embeddings file not found at {embeddings_path}")
        else:
            # Load FAISS index
            index_path = os.path.join(store_dir, 'index.faiss')
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"FAISS index not found at {index_path}")

            index = faiss.read_index(index_path)
            return index, metadata
    
    def search_similar(self, store_path: str, query: str, top_k: int = 5, 
                      context_id: Optional[int] = None,
                      operation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks with detailed logging and metrics"""
        
        if not operation_id:
            operation_id = detailed_logger.generate_operation_id()
            
        start_time = time.time()
        
        with track_operation("vector_search", 
                           query_length=len(query),
                           top_k=top_k, 
                           store_path=store_path):
            
            try:
                # Load vector store with timing
                load_start = time.time()
                index_or_embeddings, metadata = self.load_vector_store(store_path)
                load_time = time.time() - load_start
                
                store_embedding_model = metadata.get('embedding_model', 'text-embedding-004')
                total_chunks = len(metadata.get('chunks', []))
                
                logger.info(f"Vector store loaded: {total_chunks} chunks, model: {store_embedding_model}")
                
                # Create query embedding with timing
                embed_start = time.time()
                query_embedding = self.create_query_embedding(query, store_embedding_model)
                embed_time = time.time() - embed_start
                
                # Perform search with timing
                search_start = time.time()
                store_type = metadata.get('store_type', 'faiss')
                
                if store_type == 'simple' or not FAISS_AVAILABLE:
                    scores, indices = self._simple_search(query_embedding, index_or_embeddings, top_k)
                else:
                    scores, indices = index_or_embeddings.search(query_embedding, top_k)
                
                search_time = time.time() - search_start
                
                # Process results with detailed logging
                results = []
                chunks = metadata['chunks']
                total_similarity = 0
                
                for i, (score, idx) in enumerate(zip(scores[0] if len(scores.shape) > 1 else scores,
                                                   indices[0] if len(indices.shape) > 1 else indices)):
                    if idx < len(chunks):
                        chunk = chunks[idx].copy()
                        chunk_score = float(score)
                        chunk['score'] = chunk_score
                        chunk['rank'] = i + 1
                        
                        # Log individual chunk retrieval
                        chunk_metadata = chunk.get('metadata', {})
                        logger.debug(f"Retrieved chunk {i+1}: {chunk.get('source', 'unknown')} "
                                   f"score={chunk_score:.4f} size={len(chunk.get('content', ''))}")
                        
                        total_similarity += chunk_score
                        results.append(chunk)
                
                total_time = time.time() - start_time
                avg_similarity = total_similarity / len(results) if results else 0
                
                # Log comprehensive vector operation
                vector_log = VectorOperationLog(
                    operation_id=operation_id,
                    operation_type="search",
                    vector_store_path=store_path,
                    context_id=context_id or 0,
                    embedding_model=store_embedding_model,
                    operation_time=total_time,
                    search_query=query,
                    top_k=top_k,
                    results_count=len(results),
                    average_similarity=avg_similarity,
                    success=True
                )
                
                log_vector_operation(vector_log)
                
                # Log performance breakdown
                detailed_logger.log_performance_summary(operation_id, {
                    'vector_store_load_time': load_time,
                    'query_embedding_time': embed_time,
                    'similarity_search_time': search_time,
                    'total_search_time': total_time,
                    'chunks_searched': total_chunks,
                    'chunks_returned': len(results),
                    'average_similarity_score': avg_similarity
                })
                
                logger.info(f"Vector search completed: {len(results)} results in {total_time:.3f}s "
                          f"(avg similarity: {avg_similarity:.4f})")
                
                return results
                
            except Exception as e:
                total_time = time.time() - start_time
                error_msg = f"Error searching vector store: {e}"
                logger.error(error_msg)
                
                # Log failed vector operation
                vector_log = VectorOperationLog(
                    operation_id=operation_id,
                    operation_type="search",
                    vector_store_path=store_path,
                    context_id=context_id or 0,
                    embedding_model=self.embedding_model,
                    operation_time=total_time,
                    search_query=query,
                    top_k=top_k,
                    results_count=0,
                    success=False,
                    error_details=str(e)
                )
                
                log_vector_operation(vector_log)
                
                log_error_with_context(e, {
                    "operation_id": operation_id,
                    "store_path": store_path,
                    "query_length": len(query),
                    "top_k": top_k
                })
                
                return []

    def _simple_search(self, query_embedding: np.ndarray, embeddings: np.ndarray, top_k: int) -> tuple:
        """Simple similarity search using numpy (fallback when FAISS not available)"""
        # Normalize embeddings for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Calculate cosine similarity
        similarities = np.dot(embeddings_norm, query_norm.T).flatten()

        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        top_scores = similarities[top_indices]

        # Return in FAISS-like format
        return top_scores.reshape(1, -1), top_indices.reshape(1, -1)

    def add_chunks_to_store(self, store_path: str, new_chunks: List[Dict[str, Any]]) -> str:
        """Add new chunks to existing vector store"""
        try:
            # Load existing store
            index, metadata = self.load_vector_store(store_path)
            
            # Create embeddings for new chunks
            new_texts = [chunk['content'] for chunk in new_chunks]
            new_embeddings = self.create_embeddings(new_texts)
            faiss.normalize_L2(new_embeddings)
            
            # Add to index
            index.add(new_embeddings)
            
            # Update metadata
            metadata['chunks'].extend(new_chunks)
            metadata['total_chunks'] = len(metadata['chunks'])
            
            # Save updated index
            index_path = os.path.join(store_path, 'index.faiss')
            faiss.write_index(index, index_path)
            
            # Save updated metadata
            metadata_path = os.path.join(store_path, 'metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return store_path
        
        except Exception as e:
            print(f"Error adding chunks to store: {e}")
            raise e
    
    def get_store_stats(self, store_path: str) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            index, metadata = self.load_vector_store(store_path)
            
            # Calculate file type distribution
            file_types = {}
            languages = {}
            total_tokens = 0
            
            for chunk in metadata['chunks']:
                chunk_metadata = chunk.get('metadata', {})
                
                # File type distribution
                file_type = chunk_metadata.get('file_type', 'unknown')
                file_types[file_type] = file_types.get(file_type, 0) + 1
                
                # Language distribution
                language = chunk_metadata.get('language', 'unknown')
                if language != 'unknown':
                    languages[language] = languages.get(language, 0) + 1
                
                # Token count (approximate)
                content_length = len(chunk.get('content', ''))
                total_tokens += content_length // 4  # Rough token estimation
            
            return {
                'total_chunks': metadata['total_chunks'],
                'embedding_model': metadata['embedding_model'],
                'dimension': metadata['dimension'],
                'file_type_distribution': file_types,
                'language_distribution': languages,
                'estimated_tokens': total_tokens,
                'index_size': index.ntotal
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def delete_vector_store(self, store_path: str) -> bool:
        """Delete a vector store"""
        try:
            import shutil
            if os.path.exists(store_path):
                shutil.rmtree(store_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting vector store: {e}")
            return False
    
    def create_query_embedding(self, query: str, model: str = None) -> np.ndarray:
        """Create embedding for a single query using specified model"""
        target_model = model or self.embedding_model

        if target_model == 'text-embedding-004':
            try:
                from services.gemini_service import GeminiService
                gemini_service = GeminiService()
                embedding_list = gemini_service.create_query_embedding(query)
                embedding = np.array([embedding_list], dtype=np.float32)
                faiss.normalize_L2(embedding)
                return embedding
            except Exception as e:
                print(f"Error creating Gemini query embedding: {e}")

        # Fallback to sentence transformer
        if self.sentence_transformer:
            embedding = self.sentence_transformer.encode([query])
            embedding = np.array(embedding, dtype=np.float32)
            faiss.normalize_L2(embedding)
            return embedding

        raise ValueError("No embedding model available")
    
    def batch_search(self, store_path: str, queries: List[str], top_k: int = 5) -> List[List[Dict[str, Any]]]:
        """Perform batch search for multiple queries"""
        try:
            # Load vector store
            index, metadata = self.load_vector_store(store_path)

            # Get the embedding model used for this vector store
            store_embedding_model = metadata.get('embedding_model', 'text-embedding-004')

            # Create query embeddings using the same model as the store
            if store_embedding_model == 'text-embedding-004':
                # Use Gemini for query embeddings
                query_embeddings = []
                for query in queries:
                    embedding = self.create_query_embedding(query, store_embedding_model)
                    query_embeddings.append(embedding[0])  # Remove the extra dimension
                query_embeddings = np.array(query_embeddings, dtype=np.float32)
            else:
                # Use sentence transformer
                query_embeddings = self.create_embeddings(queries)
                faiss.normalize_L2(query_embeddings)

            # Search
            scores, indices = index.search(query_embeddings, top_k)

            # Prepare results for each query
            all_results = []
            chunks = metadata['chunks']

            for query_idx in range(len(queries)):
                query_results = []
                for i, (score, idx) in enumerate(zip(scores[query_idx], indices[query_idx])):
                    if idx < len(chunks):
                        chunk = chunks[idx].copy()
                        chunk['score'] = float(score)
                        chunk['rank'] = i + 1
                        chunk['query_index'] = query_idx
                        query_results.append(chunk)

                all_results.append(query_results)

            return all_results

        except Exception as e:
            print(f"Error in batch search: {e}")
            return [[] for _ in queries]

    def delete_vector_store(self, store_path: str) -> bool:
        """Delete a vector store and all associated files"""
        try:
            import shutil

            # Check if the store path exists
            if not os.path.exists(store_path):
                print(f"Vector store path does not exist: {store_path}")
                return True  # Consider it successfully deleted if it doesn't exist

            # If it's a directory, remove the entire directory
            if os.path.isdir(store_path):
                shutil.rmtree(store_path)
                print(f"Deleted vector store directory: {store_path}")
                return True

            # If it's a file, check for associated files and remove them
            base_path = store_path.replace('.index', '').replace('.metadata', '')

            # List of possible vector store files
            possible_files = [
                f"{base_path}.index",
                f"{base_path}.metadata",
                f"{store_path}",  # The original path
            ]

            deleted_files = 0
            for file_path in possible_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files += 1
                    print(f"Deleted vector store file: {file_path}")

            return deleted_files > 0

        except Exception as e:
            print(f"Error deleting vector store {store_path}: {e}")
            return False

    def get_vector_store_info(self, store_path: str) -> Dict[str, Any]:
        """Get information about a vector store"""
        try:
            index, metadata = self.load_vector_store(store_path)

            return {
                'total_chunks': len(metadata['chunks']),
                'embedding_model': metadata.get('embedding_model', 'unknown'),
                'created_at': metadata.get('created_at', 'unknown'),
                'dimension': index.d if index else 0
            }

        except Exception as e:
            print(f"Error getting vector store info: {e}")
            return {}
