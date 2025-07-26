"""
LLM service for Gemini integration
"""

import os
import json
from typing import List, Dict, Any, Generator, Optional
import google.generativeai as genai

class LLMService:
    """Service for LLM interactions using Gemini"""
    
    def __init__(self, model_name: str = 'gemini-pro'):
        self.model_name = model_name
        self.client = None
        self.model = None
        
        # Initialize Gemini
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            
            genai.configure(api_key=api_key)
            self.client = genai
            self.model = genai.GenerativeModel(self.model_name)
            
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            raise e
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], 
                         chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a response using RAG context"""
        try:
            # Prepare context
            context = self._prepare_context(context_chunks)
            
            # Create prompt
            prompt = self._create_rag_prompt(query, context, chat_history)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Count tokens (approximate)
            tokens_used = self._estimate_tokens(prompt + response.text)
            
            return {
                'content': response.text,
                'tokens_used': tokens_used,
                'model_used': self.model_name,
                'context_chunks_used': len(context_chunks)
            }
        
        except Exception as e:
            return {
                'content': f"Error generating response: {str(e)}",
                'tokens_used': 0,
                'model_used': self.model_name,
                'error': True
            }
    
    def generate_streaming_response(self, query: str, context_chunks: List[Dict[str, Any]], 
                                  chat_history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        """Generate a streaming response using RAG context"""
        try:
            # Prepare context
            context = self._prepare_context(context_chunks)
            
            # Create prompt
            prompt = self._create_rag_prompt(query, context, chat_history)
            
            # Generate streaming response
            response = self.model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            yield f"Error generating streaming response: {str(e)}"
    
    def _prepare_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved chunks"""
        if not context_chunks:
            return "No relevant context found."
        
        context_parts = []
        
        for i, chunk in enumerate(context_chunks):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            # Add source information
            source_info = []
            if 'file_path' in metadata:
                source_info.append(f"File: {metadata['file_path']}")
            if 'language' in metadata:
                source_info.append(f"Language: {metadata['language']}")
            if 'chunk_index' in metadata:
                source_info.append(f"Chunk: {metadata['chunk_index']}")
            
            source_str = " | ".join(source_info) if source_info else "Unknown source"
            
            context_parts.append(f"[Source {i+1}: {source_str}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Create a RAG prompt with context and chat history"""
        
        # System prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 
        
Guidelines:
1. Use the provided context to answer the question accurately
2. If the context doesn't contain enough information, say so clearly
3. Cite specific sources when possible using [Source X] notation
4. Provide code examples when relevant and available in the context
5. Be concise but comprehensive
6. If asked about code, explain both what it does and how it works
7. For database-related questions, provide schema information when available

Context:
{context}

"""
        
        # Add chat history if provided
        conversation = ""
        if chat_history:
            conversation = "\nPrevious conversation:\n"
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                conversation += f"{role.capitalize()}: {content}\n"
            conversation += "\n"
        
        # Current question
        current_question = f"Current question: {query}\n\nAnswer:"
        
        return system_prompt.format(context=context) + conversation + current_question
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def summarize_document(self, content: str, max_length: int = 500) -> str:
        """Summarize a document or chunk"""
        try:
            prompt = f"""Please provide a concise summary of the following content in no more than {max_length} characters:

Content:
{content}

Summary:"""
            
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            return f"Error summarizing content: {str(e)}"
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content"""
        try:
            prompt = f"""Extract the {max_keywords} most important keywords or phrases from the following content. 
            Return them as a comma-separated list:

Content:
{content}

Keywords:"""
            
            response = self.model.generate_content(prompt)
            keywords = [kw.strip() for kw in response.text.split(',')]
            return keywords[:max_keywords]
        
        except Exception as e:
            return [f"Error extracting keywords: {str(e)}"]
    
    def generate_title(self, content: str) -> str:
        """Generate a title for content"""
        try:
            prompt = f"""Generate a concise, descriptive title for the following content (max 10 words):

Content:
{content[:1000]}...

Title:"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            return "Untitled Content"
    
    def classify_content(self, content: str, categories: List[str]) -> str:
        """Classify content into one of the provided categories"""
        try:
            categories_str = ", ".join(categories)
            prompt = f"""Classify the following content into one of these categories: {categories_str}

Content:
{content[:1000]}...

Category:"""
            
            response = self.model.generate_content(prompt)
            classification = response.text.strip()
            
            # Ensure the response is one of the valid categories
            for category in categories:
                if category.lower() in classification.lower():
                    return category
            
            return categories[0] if categories else "Unknown"
        
        except Exception as e:
            return "Unknown"
    
    def explain_code(self, code: str, language: str = None) -> str:
        """Explain what a piece of code does"""
        try:
            lang_info = f" (written in {language})" if language else ""
            prompt = f"""Explain what the following code{lang_info} does in simple terms:

Code:
{code}

Explanation:"""
            
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            return f"Error explaining code: {str(e)}"
    
    def generate_sql_query(self, natural_language: str, schema_info: str) -> str:
        """Generate SQL query from natural language description"""
        try:
            prompt = f"""Given the following database schema, generate a SQL query for the request:

Schema:
{schema_info}

Request: {natural_language}

SQL Query:"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            return f"-- Error generating SQL: {str(e)}"
    
    def improve_prompt(self, original_prompt: str) -> str:
        """Improve a user's prompt for better results"""
        try:
            prompt = f"""Improve the following prompt to make it more specific and likely to get better results:

Original prompt: {original_prompt}

Improved prompt:"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            return original_prompt
    
    def check_content_safety(self, content: str) -> Dict[str, Any]:
        """Check if content is safe and appropriate"""
        try:
            # Use Gemini's built-in safety features
            response = self.model.generate_content(content)
            
            # Check if response was blocked
            if hasattr(response, 'prompt_feedback'):
                safety_ratings = response.prompt_feedback.safety_ratings
                blocked = any(rating.probability.name in ['HIGH', 'MEDIUM'] for rating in safety_ratings)
                
                return {
                    'is_safe': not blocked,
                    'safety_ratings': [
                        {
                            'category': rating.category.name,
                            'probability': rating.probability.name
                        } for rating in safety_ratings
                    ]
                }
            
            return {'is_safe': True, 'safety_ratings': []}
        
        except Exception as e:
            return {'is_safe': False, 'error': str(e)}
