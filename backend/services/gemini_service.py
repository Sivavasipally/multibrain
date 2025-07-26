"""
Enhanced Gemini service with embeddings and advanced RAG capabilities
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Generator, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiService:
    """Enhanced service for Gemini LLM and embedding integration"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        self.chat_model = genai.GenerativeModel('gemini-1.5-flash')
        self.embedding_model = 'models/text-embedding-004'
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    def create_embeddings(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """Create embeddings for a list of texts with retry logic"""
        embeddings = []

        for i, text in enumerate(texts):
            print(f"Creating embedding {i+1}/{len(texts)}")

            # Truncate very long texts to avoid API limits
            if len(text) > 8000:  # Conservative limit
                text = text[:8000] + "..."

            success = False
            for attempt in range(3):  # 3 retry attempts
                try:
                    result = genai.embed_content(
                        model=self.embedding_model,
                        content=text,
                        task_type=task_type
                    )
                    embeddings.append(result['embedding'])
                    success = True
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for embedding {i+1}: {e}")
                    if attempt < 2:  # Don't sleep on last attempt
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s

            if not success:
                print(f"Failed to create embedding for text {i+1}, using zero vector")
                # Return zero vector as fallback
                embeddings.append([0.0] * 768)  # text-embedding-004 dimension

        return embeddings
    
    def create_query_embedding(self, query: str) -> List[float]:
        """Create embedding for a search query"""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error creating query embedding: {e}")
            return [0.0] * 768
    
    def generate_response(self, 
                         query: str, 
                         context_chunks: List[Dict[str, Any]], 
                         chat_history: List[Dict[str, str]] = None,
                         max_tokens: int = 2048) -> Dict[str, Any]:
        """Generate response using Gemini with RAG context"""
        
        # Prepare context from chunks
        context_text = self._prepare_context(context_chunks)
        
        # Prepare chat history
        history_text = self._prepare_history(chat_history) if chat_history else ""
        
        # Create the prompt
        prompt = self._create_rag_prompt(query, context_text, history_text)
        
        try:
            response = self.chat_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            return {
                'content': response.text,
                'model_used': 'gemini-1.5-flash',
                'tokens_used': self._estimate_tokens(response.text),
                'citations': self._extract_citations(context_chunks)
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'content': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'model_used': 'gemini-1.5-flash',
                'tokens_used': 0,
                'citations': []
            }
    
    def generate_streaming_response(self, 
                                   query: str, 
                                   context_chunks: List[Dict[str, Any]], 
                                   chat_history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        """Generate streaming response using Gemini"""
        
        # Prepare context and prompt
        context_text = self._prepare_context(context_chunks)
        history_text = self._prepare_history(chat_history) if chat_history else ""
        prompt = self._create_rag_prompt(query, context_text, history_text)
        
        try:
            response = self.chat_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40
                ),
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def summarize_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive summary of multiple documents"""
        
        # Prepare document content
        doc_content = []
        for doc in documents:
            content = doc.get('content', '')
            source = doc.get('source', 'Unknown')
            doc_content.append(f"## Document: {source}\n{content[:2000]}...")
        
        combined_content = "\n\n".join(doc_content)
        
        prompt = f"""
        Please provide a comprehensive summary of the following documents. 
        Include key points, main themes, and important details from each document.
        
        Documents:
        {combined_content}
        
        Summary:
        """
        
        try:
            response = self.chat_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1024,
                    temperature=0.5
                )
            )
            
            return response.text
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _prepare_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context text from chunks"""
        if not context_chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(context_chunks[:10]):  # Limit to top 10 chunks
            content = chunk.get('content', '')
            source = chunk.get('source', f'Source {i+1}')
            context_parts.append(f"[{i+1}] From {source}:\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _prepare_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Prepare chat history for context"""
        if not chat_history:
            return ""
        
        history_parts = []
        for msg in chat_history[-5:]:  # Last 5 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            history_parts.append(f"{role.title()}: {content}")
        
        return "\n".join(history_parts)
    
    def _create_rag_prompt(self, query: str, context: str, history: str) -> str:
        """Create RAG prompt with context and history"""
        
        prompt_parts = [
            "You are a helpful AI assistant with access to relevant documents and context.",
            "Use the provided context to answer questions accurately and cite your sources.",
            "If the context doesn't contain enough information, say so clearly.",
            ""
        ]
        
        if history:
            prompt_parts.extend([
                "Previous conversation:",
                history,
                ""
            ])
        
        if context:
            prompt_parts.extend([
                "Relevant context:",
                context,
                ""
            ])
        
        prompt_parts.extend([
            f"Question: {query}",
            "",
            "Answer:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_citations(self, context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citation information from context chunks"""
        citations = []
        for i, chunk in enumerate(context_chunks):
            citations.append({
                'id': i + 1,
                'source': chunk.get('source', f'Source {i+1}'),
                'content_preview': chunk.get('content', '')[:100] + '...',
                'score': chunk.get('score', 0.0)
            })
        return citations
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text.split()) * 1.3  # Rough estimate
