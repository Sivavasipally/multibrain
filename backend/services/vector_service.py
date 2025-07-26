"""
Vector storage service using FAISS
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional

# Optional imports with fallbacks
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available. Vector search will be disabled.")

# Check if sentence transformers is available without importing
try:
    import importlib.util
    spec = importlib.util.find_spec("sentence_transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = spec is not None
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

if not SENTENCE_TRANSFORMERS_AVAILABLE:
    print("Warning: Sentence Transformers not available. Using basic embeddings.")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Google Generative AI not available.")

class VectorService:
    """Service for vector storage and similarity search using FAISS"""
    
    def __init__(self, embedding_model: str = 'text-embedding-004'):
        self.embedding_model = embedding_model
        self.sentence_transformer = None
        self.gemini_client = None
        
        # Initialize embedding models
        self._init_embedding_models()
    
    def _init_embedding_models(self):
        """Initialize embedding models"""
        try:
            # Initialize Sentence Transformers for local embeddings
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    from sentence_transformers import SentenceTransformer
                    self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                except Exception as e:
                    print(f"Warning: Failed to initialize Sentence Transformers: {e}")
                    self.sentence_transformer = None
            else:
                print("Warning: Sentence Transformers not available")

            # Initialize Gemini for text-embedding-004
            if self.embedding_model == 'text-embedding-004' and GEMINI_AVAILABLE:
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.gemini_client = genai
                else:
                    print("Warning: GEMINI_API_KEY not found in environment")
            elif not GEMINI_AVAILABLE:
                print("Warning: Google Generative AI not available")

        except Exception as e:
            print(f"Warning: Could not initialize embedding models: {e}")
    
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
        metadata_path = os.path.join(store_path, 'metadata.json')

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Vector store metadata not found at {store_path}")

        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Check store type
        store_type = metadata.get('store_type', 'faiss')

        if store_type == 'simple' or not FAISS_AVAILABLE:
            # Load simple store (just embeddings)
            embeddings_path = os.path.join(store_path, 'embeddings.npy')
            if os.path.exists(embeddings_path):
                embeddings = np.load(embeddings_path)
                return embeddings, metadata
            else:
                raise FileNotFoundError(f"Embeddings file not found at {embeddings_path}")
        else:
            # Load FAISS index
            index_path = os.path.join(store_path, 'index.faiss')
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"FAISS index not found at {index_path}")

            index = faiss.read_index(index_path)
            return index, metadata
    
    def search_similar(self, store_path: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks in the vector store"""
        try:
            # Load vector store
            index_or_embeddings, metadata = self.load_vector_store(store_path)

            # Get the embedding model used for this vector store
            store_embedding_model = metadata.get('embedding_model', 'text-embedding-004')
            print(f"Vector store uses embedding model: {store_embedding_model}")
            print(f"Total chunks in store: {len(metadata.get('chunks', []))}")

            # Create query embedding using the same model as the store
            query_embedding = self.create_query_embedding(query, store_embedding_model)

            # Check store type
            store_type = metadata.get('store_type', 'faiss')

            if store_type == 'simple' or not FAISS_AVAILABLE:
                # Simple similarity search using numpy
                scores, indices = self._simple_search(query_embedding, index_or_embeddings, top_k)
            else:
                # FAISS search
                scores, indices = index_or_embeddings.search(query_embedding, top_k)

            # Prepare results
            results = []
            chunks = metadata['chunks']

            for i, (score, idx) in enumerate(zip(scores[0] if len(scores.shape) > 1 else scores,
                                               indices[0] if len(indices.shape) > 1 else indices)):
                if idx < len(chunks):
                    chunk = chunks[idx].copy()
                    chunk['score'] = float(score)
                    chunk['rank'] = i + 1
                    # Add debug info about the chunk
                    chunk_metadata = chunk.get('metadata', {})
                    print(f"Retrieved chunk {i+1}: file_type={chunk_metadata.get('file_type', 'unknown')}, score={score:.4f}")
                    results.append(chunk)

            return results

        except Exception as e:
            print(f"Error searching vector store: {e}")
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
