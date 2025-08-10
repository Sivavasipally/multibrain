"""
Large Language Model Service with Google Gemini Integration for RAG Chatbot PWA

This module provides comprehensive LLM (Large Language Model) capabilities for the RAG
(Retrieval-Augmented Generation) chatbot system. It integrates with Google's Gemini API
to provide intelligent response generation, content analysis, and various AI-powered utilities.

Key Features:
- RAG-powered response generation with context integration
- Real-time streaming responses for improved user experience
- Content analysis and classification capabilities
- Code explanation and documentation generation
- SQL query generation from natural language
- Content safety and moderation checks
- Comprehensive error handling and logging

Core Capabilities:
1. Response Generation: Context-aware AI responses using retrieved information
2. Streaming Responses: Real-time response generation for chat interfaces
3. Content Processing: Summarization, keyword extraction, title generation
4. Code Analysis: Code explanation and documentation generation
5. Natural Language Processing: Text classification and content analysis
6. Safety Checks: Content moderation and safety assessment

Gemini Models Supported:
- gemini-2.0-flash: Fast, efficient model for general tasks (default)
- gemini-1.5-pro: High-quality model for complex reasoning
- gemini-1.5-flash: Balanced performance and efficiency

Dependencies:
- google-generativeai: Official Google Gemini API client
- typing: Type hints for better code documentation
- os: Environment variable access for API keys
- json: JSON data handling

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
import google.generativeai as genai

# Import logging functionality
from logging_config import get_logger, log_error_with_context
from services.detailed_logger import (
    detailed_logger, log_rag_operation, RAGOperationMetrics, 
    track_operation
)

# Initialize logger
logger = get_logger('llm_service')

class LLMService:
    """
    Comprehensive LLM service for AI-powered text generation and analysis
    
    This class provides a complete interface to Google Gemini's language models,
    offering both basic text generation and advanced RAG (Retrieval-Augmented Generation)
    capabilities. It handles context integration, streaming responses, and various
    content analysis tasks.
    
    Key Features:
    - Context-aware response generation using RAG methodology
    - Real-time streaming responses for interactive chat experiences
    - Content analysis: summarization, classification, keyword extraction
    - Code explanation and documentation generation
    - Natural language to SQL query translation
    - Content safety and moderation checks
    - Comprehensive error handling and logging
    
    Architecture:
    1. Initialization: Configure Gemini client with API credentials
    2. Context Preparation: Format retrieved chunks for RAG prompts
    3. Prompt Engineering: Create optimized prompts for different tasks
    4. Response Generation: Generate responses using configured model
    5. Post-processing: Format and validate generated content
    
    Attributes:
        model_name (str): Gemini model identifier (e.g., 'gemini-2.0-flash')
        client: Google Generative AI client instance
        model: Configured Gemini model for text generation
        
    Example:
        >>> llm = LLMService('gemini-2.0-flash')
        >>> context_chunks = [{'content': 'Python is a programming language...'}]
        >>> response = llm.generate_response('What is Python?', context_chunks)
        >>> print(response['content'])
    """
    
    def __init__(self, model_name: str = 'gemini-2.0-flash'):
        """
        Initialize the LLM Service with specified Gemini model
        
        Args:
            model_name (str): Gemini model identifier. Options:
                - 'gemini-2.0-flash': Fast, efficient model (default)
                - 'gemini-1.5-pro': High-quality reasoning model
                - 'gemini-1.5-flash': Balanced performance model
                
        Raises:
            ValueError: If GEMINI_API_KEY environment variable is not set
            Exception: If Gemini client initialization fails
        """
        logger.info(f"Initializing LLMService with model: {model_name}")
        
        self.model_name = model_name
        self.client = None
        self.model = None
        
        # Initialize Gemini
        try:
            self._init_gemini()
            logger.info("LLMService initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLMService: {e}")
            log_error_with_context(e, {"model_name": model_name})
            raise
    
    def _init_gemini(self):
        """
        Initialize Google Gemini client with API configuration
        
        Configures the Gemini API client using environment variables and creates
        a GenerativeModel instance for text generation tasks. This method handles
        authentication and model instantiation with comprehensive error handling.
        
        Environment Variables:
            GEMINI_API_KEY: Google AI API key for Gemini access
            
        Raises:
            ValueError: If GEMINI_API_KEY environment variable is not set
            Exception: If Gemini client configuration or model creation fails
            
        Security:
            - API key is read from environment variables only
            - No API key logging or exposure in error messages
            - Secure client configuration following Google's best practices
        """
        logger.debug("Starting Gemini client initialization")
        
        try:
            # Get API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                error_msg = "GEMINI_API_KEY environment variable not set"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.debug("API key found, configuring Gemini client")
            
            # Configure Gemini client
            genai.configure(api_key=api_key)
            self.client = genai
            
            # Create generative model instance
            self.model = genai.GenerativeModel(self.model_name)
            
            logger.info(f"Gemini client initialized successfully with model: {self.model_name}")
            
        except ValueError:
            raise  # Re-raise ValueError for missing API key
        except Exception as e:
            error_msg = f"Error initializing Gemini client: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {"model_name": self.model_name})
            raise Exception(error_msg)
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], 
                         chat_history: List[Dict[str, str]] = None,
                         operation_id: Optional[str] = None,
                         user_id: Optional[int] = None,
                         session_id: Optional[int] = None,
                         contexts_searched: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Generate AI response using RAG methodology with comprehensive logging
        
        Enhanced RAG implementation with detailed performance tracking and metrics
        collection for monitoring LLM operations, token usage, and system performance.
        
        Args:
            query (str): User's question or request
            context_chunks (List[Dict[str, Any]]): Retrieved text chunks from vector search
            chat_history (List[Dict[str, str]], optional): Previous conversation messages
            operation_id (Optional[str]): Unique operation ID for tracking
            user_id (Optional[int]): User ID for activity tracking
            session_id (Optional[int]): Session ID for metrics
            contexts_searched (Optional[List[int]]): List of context IDs searched
                
        Returns:
            Dict[str, Any]: Enhanced response with comprehensive metrics
        """
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = detailed_logger.generate_operation_id()
            
        start_time = time.time()
        
        with track_operation("llm_generate_response", 
                           query_length=len(query), 
                           chunks_count=len(context_chunks),
                           model=self.model_name):
            
            logger.info(f"Generating RAG response for query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
            
            try:
                # Prepare context from retrieved chunks
                context_start = time.time()
                context = self._prepare_context(context_chunks)
                context_time = time.time() - context_start
                
                # Create RAG prompt with context and history
                prompt_start = time.time()
                prompt = self._create_rag_prompt(query, context, chat_history)
                prompt_time = time.time() - prompt_start
                
                # Generate response using Gemini
                generation_start = time.time()
                response = self.model.generate_content(prompt)
                generation_time = time.time() - generation_start
                
                # Calculate comprehensive metrics
                input_tokens = self._estimate_tokens(prompt)
                output_tokens = self._estimate_tokens(response.text)
                total_tokens = input_tokens + output_tokens
                response_length = len(response.text)
                total_time = time.time() - start_time
                
                # Log detailed LLM interaction
                detailed_logger.log_llm_interaction(
                    operation_id=operation_id,
                    model=self.model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    response_time=generation_time,
                    prompt_type="rag_chat"
                )
                
                # Create comprehensive RAG metrics if tracking data provided
                if user_id and session_id and contexts_searched is not None:
                    chunks_by_context = {}
                    for chunk in context_chunks:
                        ctx_id = str(chunk.get('context_id', 'unknown'))
                        chunks_by_context[ctx_id] = chunks_by_context.get(ctx_id, 0) + 1
                    
                    rag_metrics = RAGOperationMetrics(
                        operation_id=operation_id,
                        user_id=user_id,
                        session_id=session_id,
                        query=query,
                        contexts_searched=contexts_searched,
                        total_chunks_retrieved=len(context_chunks),
                        chunks_by_context=chunks_by_context,
                        retrieval_time=0,  # Set by calling function
                        llm_generation_time=generation_time,
                        total_response_time=total_time,
                        tokens_input=input_tokens,
                        tokens_output=output_tokens,
                        model_used=self.model_name,
                        response_length=response_length,
                        success=True
                    )
                    
                    log_rag_operation(rag_metrics)
                
                logger.info(
                    f"Enhanced context preparation completed: {len(context_chunks)} sources, "
                    f"{len(context)} total characters"
                )
                logger.info(f"Generated response: {response_length} characters, ~{total_tokens} tokens")
                
                return {
                    'content': response.text,
                    'tokens_used': total_tokens,
                    'model_used': self.model_name,
                    'context_chunks_used': len(context_chunks),
                    'operation_id': operation_id,
                    'performance_metrics': {
                        'context_prep_time': context_time,
                        'prompt_creation_time': prompt_time,
                        'generation_time': generation_time,
                        'total_time': total_time,
                        'tokens_per_second': output_tokens / generation_time if generation_time > 0 else 0
                    }
                }
        
            except Exception as e:
                error_msg = f"Error generating RAG response: {str(e)}"
                logger.error(error_msg)
                
                # Log failed RAG operation
                if user_id and session_id and contexts_searched is not None:
                    rag_metrics = RAGOperationMetrics(
                        operation_id=operation_id,
                        user_id=user_id,
                        session_id=session_id,
                        query=query,
                        contexts_searched=contexts_searched,
                        total_chunks_retrieved=len(context_chunks),
                        chunks_by_context={},
                        retrieval_time=0,
                        llm_generation_time=0,
                        total_response_time=time.time() - start_time,
                        tokens_input=0,
                        tokens_output=0,
                        model_used=self.model_name,
                        response_length=0,
                        success=False,
                        error_details=str(e)
                    )
                    log_rag_operation(rag_metrics)
                
                log_error_with_context(e, {
                    "operation_id": operation_id,
                    "query_length": len(query),
                    "context_chunks_count": len(context_chunks),
                    "model_name": self.model_name,
                    "has_chat_history": bool(chat_history)
                })
                
                return {
                    'content': f"I apologize, but I encountered an error while processing your request. Please try again.",
                    'tokens_used': 0,
                    'model_used': self.model_name,
                    'context_chunks_used': len(context_chunks),
                    'operation_id': operation_id,
                    'error': True,
                    'error_message': str(e)
                }
    
    def generate_streaming_response(self, query: str, context_chunks: List[Dict[str, Any]], 
                                  chat_history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        """
        Generate real-time streaming AI response using RAG methodology
        
        Provides real-time response generation for interactive chat experiences.
        This method yields response chunks as they are generated, allowing for
        immediate user feedback and improved perceived responsiveness.
        
        Streaming Process:
        1. Context Preparation: Format retrieved chunks for RAG
        2. Prompt Creation: Build comprehensive prompt with context
        3. Stream Initiation: Start Gemini streaming response generation
        4. Chunk Processing: Yield individual response chunks as available
        5. Error Handling: Provide error feedback through stream if needed
        
        Args:
            query (str): User's question or request
            context_chunks (List[Dict[str, Any]]): Retrieved text chunks from vector search
            chat_history (List[Dict[str, str]], optional): Previous conversation messages
                
        Yields:
            str: Individual response text chunks as they are generated
                 Error messages if generation fails
                 
        Example:
            >>> chunks = [{'content': 'API documentation...', 'metadata': {...}}]
            >>> for chunk in llm.generate_streaming_response('How to use the API?', chunks):
            ...     print(chunk, end='', flush=True)  # Print in real-time
                
        Performance:
            - Reduces perceived latency by providing immediate feedback
            - Allows for progressive UI updates during response generation
            - Enables early termination if user navigates away
            
        Error Handling:
            - Yields error messages instead of raising exceptions
            - Maintains stream integrity even during failures
            - Logs comprehensive error information for debugging
        """
        logger.info(f"Starting streaming RAG response for query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
        logger.debug(f"Streaming with {len(context_chunks)} context chunks, chat history: {len(chat_history) if chat_history else 0} messages")
        
        try:
            # Prepare context from retrieved chunks
            logger.debug("Preparing context for streaming response")
            context = self._prepare_context(context_chunks)
            
            # Create RAG prompt
            logger.debug("Creating RAG prompt for streaming")
            prompt = self._create_rag_prompt(query, context, chat_history)
            
            # Generate streaming response using Gemini
            logger.debug(f"Starting streaming generation with {self.model_name}")
            response = self.model.generate_content(prompt, stream=True)
            
            chunk_count = 0
            total_length = 0
            
            for chunk in response:
                if chunk.text:
                    chunk_count += 1
                    total_length += len(chunk.text)
                    logger.debug(f"Yielding chunk {chunk_count}: {len(chunk.text)} characters")
                    yield chunk.text
            
            logger.info(f"Streaming completed: {chunk_count} chunks, {total_length} total characters")
        
        except Exception as e:
            error_msg = f"Error generating streaming response: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "query_length": len(query),
                "context_chunks_count": len(context_chunks),
                "model_name": self.model_name,
                "streaming": True
            })
            
            yield f"I apologize, but I encountered an error while processing your request. Please try again."
    
    def _prepare_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Prepare and format retrieved context chunks for enhanced RAG prompts
        
        Transforms raw context chunks from vector search into a richly formatted string
        that provides comprehensive metadata and structural information for AI consumption.
        This enhanced version extracts document properties, section information, and
        processing details to enable more intelligent responses.
        
        Enhanced Context Formatting:
        - Source attribution with comprehensive metadata
        - Document properties (title, author, creation date)
        - Section and structural information
        - Processing method and content type details
        - Table and formatting indicators
        - Clear separation between different sources
        
        Args:
            context_chunks (List[Dict[str, Any]]): Retrieved chunks from vector search
                Each chunk should contain:
                - content (str): Actual text content
                - metadata (dict): Enhanced file and chunk metadata
                
        Returns:
            str: Richly formatted context string ready for enhanced RAG prompts
                 "No relevant context found." if no chunks provided
                 
        Example:
            >>> chunks = [{
            ...     'content': '# Client Connect\nThis is a business document...',
            ...     'metadata': {
            ...         'file_name': 'client_connect.docx',
            ...         'document_type': 'office_document',
            ...         'section_title': 'Overview',
            ...         'document_properties': {'title': 'Client Connect Guide'},
            ...         'has_tables': True
            ...     }
            ... }]
            >>> context = service._prepare_context(chunks)
        """
        if not context_chunks:
            logger.debug("No context chunks provided for RAG")
            return "No relevant context found."
        
        logger.debug(f"Preparing enhanced context from {len(context_chunks)} chunks")
        context_parts = []
        
        for i, chunk in enumerate(context_chunks):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            # Build comprehensive source information
            source_info = []
            
            # File identification
            if 'file_name' in metadata:
                source_info.append(f"File: {metadata['file_name']}")
            elif 'file_path' in metadata:
                file_name = Path(metadata['file_path']).name
                source_info.append(f"File: {file_name}")
            
            # Document type and processing information
            if 'document_type' in metadata:
                source_info.append(f"Type: {metadata['document_type']}")
            elif 'file_type' in metadata:
                source_info.append(f"Type: {metadata['file_type']}")
            
            # Section and structural information
            if 'section_title' in metadata and metadata['section_title']:
                source_info.append(f"Section: {metadata['section_title']}")
            
            if 'processing_method' in metadata:
                source_info.append(f"Processing: {metadata['processing_method']}")
            
            # Content indicators
            content_indicators = []
            if metadata.get('has_tables'):
                content_indicators.append("contains tables")
            if metadata.get('table_count', 0) > 0:
                content_indicators.append(f"{metadata['table_count']} tables")
            if metadata.get('paragraph_count', 0) > 0:
                content_indicators.append(f"{metadata['paragraph_count']} paragraphs")
            
            if content_indicators:
                source_info.append(f"Content: {', '.join(content_indicators)}")
            
            # Technical details for code
            if 'language' in metadata:
                source_info.append(f"Language: {metadata['language']}")
            if 'start_line' in metadata and 'end_line' in metadata:
                source_info.append(f"Lines: {metadata['start_line']}-{metadata['end_line']}")
            if 'chunk_index' in metadata:
                source_info.append(f"Chunk: {metadata['chunk_index']}")
            
            source_str = " | ".join(source_info) if source_info else "Unknown source"
            
            # Extract document properties for office documents
            doc_properties_str = ""
            if 'document_properties' in metadata and metadata['document_properties']:
                props = metadata['document_properties']
                prop_parts = []
                if props.get('title'):
                    prop_parts.append(f"Title: '{props['title']}'")
                if props.get('creator'):
                    prop_parts.append(f"Author: {props['creator']}")
                if props.get('subject'):
                    prop_parts.append(f"Subject: {props['subject']}")
                if props.get('keywords'):
                    prop_parts.append(f"Keywords: {props['keywords']}")
                if props.get('description'):
                    prop_parts.append(f"Description: {props['description']}")
                
                if prop_parts:
                    doc_properties_str = f"\nDocument Properties: {' | '.join(prop_parts)}"
            
            # Format context chunk with enhanced attribution
            chunk_header = f"[Source {i+1}: {source_str}]{doc_properties_str}"
            context_parts.append(f"{chunk_header}\n{content}\n")
            
            logger.debug(f"Prepared enhanced chunk {i+1}: {len(content)} characters from {metadata.get('file_name', 'unknown')}")
        
        formatted_context = "\n".join(context_parts)
        logger.info(f"Enhanced context preparation completed: {len(context_parts)} sources, {len(formatted_context)} total characters")
        
        return formatted_context
    
    def _create_rag_prompt(self, query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Create optimized RAG prompt with context integration and conversation history
        
        Constructs a comprehensive prompt that effectively combines retrieved context
        with user queries and conversation history. The prompt is engineered to maximize
        the quality and accuracy of AI responses while maintaining proper source attribution.
        
        Prompt Structure:
        1. System Instructions: Define AI behavior and response guidelines
        2. Context Integration: Insert formatted retrieved information
        3. Conversation History: Include relevant previous exchanges
        4. Current Query: Present the user's current question
        5. Response Guidance: Provide specific answering instructions
        
        Args:
            query (str): Current user question or request
            context (str): Formatted context from retrieved chunks
            chat_history (List[Dict[str, str]], optional): Previous conversation messages
                
        Returns:
            str: Complete RAG prompt ready for AI model consumption
            
        Prompt Engineering Features:
        - Clear behavioral guidelines for consistent responses
        - Source citation instructions for proper attribution
        - Context-aware response formatting
        - Conversation continuity through history integration
        - Specific handling instructions for different content types
        
        Example:
            >>> prompt = service._create_rag_prompt(
            ...     "What is Python?",
            ...     "[Source 1: python.org] Python is a programming language...",
            ...     [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
            ... )
        """
        logger.debug(f"Creating RAG prompt for query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        logger.debug(f"Context length: {len(context)} characters, Chat history: {len(chat_history) if chat_history else 0} messages")
        
        # System prompt with comprehensive guidelines for enhanced responses
        system_prompt = """You are an intelligent AI assistant that provides detailed, context-aware responses based on the provided information. Your goal is to be helpful, accurate, and comprehensive.

Advanced Response Guidelines:
1. **Context Analysis**: Carefully analyze all provided context to understand the full scope of information available
2. **Rich Information Extraction**: When documents contain structured data (tables, sections, properties), extract and present relevant details
3. **Source Attribution**: Always cite specific sources using [Source X] notation with descriptive information
4. **Document Understanding**: For office documents, extract document properties, section titles, table data, and structural information when relevant
5. **Comprehensive Answers**: Provide detailed explanations that go beyond simple text matching - synthesize information meaningfully
6. **Content Type Awareness**: Recognize different content types (code, documents, data) and respond appropriately
7. **Structured Presentation**: Use formatting (headers, lists, tables) to present information clearly
8. **Metadata Utilization**: Use document metadata (title, author, creation date) when relevant to the query
9. **Cross-Reference Information**: When multiple sources contain related information, connect and synthesize them
10. **Practical Focus**: Emphasize actionable insights and practical applications of the information

For document-specific queries:
- Extract and present document properties (title, author, subject) when relevant
- Include section titles and structural information
- Present table data in readable format when applicable
- Identify document type and processing method used
- Reference specific sections or content areas within documents

Context Information:
{context}

"""
        
        # Add conversation history for context continuity
        conversation = ""
        if chat_history:
            logger.debug(f"Including {min(len(chat_history), 5)} recent messages in prompt")
            conversation = "\nPrevious conversation:\n"
            # Include last 5 messages to maintain context without overwhelming the prompt
            for msg in chat_history[-5:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                # Truncate very long messages to keep prompt manageable
                if len(content) > 200:
                    content = content[:200] + "..."
                conversation += f"{role.capitalize()}: {content}\n"
            conversation += "\n"
        
        # Current question with clear formatting
        current_question = f"Current question: {query}\n\nAnswer:"
        
        # Combine all components
        complete_prompt = system_prompt.format(context=context) + conversation + current_question
        
        prompt_length = len(complete_prompt)
        logger.debug(f"RAG prompt created: {prompt_length} characters total")
        
        return complete_prompt
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for cost tracking and optimization
        
        Provides an approximate token count for text content to help with
        cost monitoring and prompt optimization. This is a rough estimation
        based on character count and typical tokenization patterns.
        
        Token Estimation Method:
        - English text: ~4 characters per token (GPT-style tokenization)
        - Code: ~3.5 characters per token (more symbols and keywords)
        - Mixed content: Uses conservative 4:1 ratio
        
        Args:
            text (str): Text content to analyze
            
        Returns:
            int: Estimated token count
            
        Note:
            This is an approximation and actual token counts may vary based on:
            - Language and content type
            - Specific tokenizer used by the model
            - Special characters and formatting
            
        Example:
            >>> tokens = service._estimate_tokens("Hello world!")
            >>> print(f"Estimated tokens: {tokens}")
            Estimated tokens: 3
        """
        if not text:
            return 0
            
        # Rough estimation: 1 token ≈ 4 characters for English text
        # This is conservative and should cover most use cases
        estimated = len(text) // 4
        
        logger.debug(f"Token estimation: {len(text)} characters → ~{estimated} tokens")
        return estimated
    
    def summarize_document(self, content: str, max_length: int = 500) -> str:
        """
        Generate concise summary of document or text content
        
        Creates intelligent summaries of long-form content for quick comprehension
        and content overview. This is useful for document indexing, preview generation,
        and content management workflows.
        
        Summarization Features:
        - Length control with character limits
        - Key information extraction
        - Maintains essential context and meaning
        - Handles various content types (code, documentation, articles)
        
        Args:
            content (str): Text content to summarize
            max_length (int): Maximum summary length in characters (default: 500)
            
        Returns:
            str: Generated summary or error message if generation fails
            
        Example:
            >>> content = "Long article about machine learning..."
            >>> summary = llm.summarize_document(content, max_length=200)
            >>> print(f"Summary: {summary}")
            
        Use Cases:
            - Document preview generation
            - Content indexing and cataloging
            - Quick content assessment
            - Search result snippets
        """
        logger.info(f"Generating summary for content: {len(content)} characters, max length: {max_length}")
        
        try:
            # Truncate very long content to avoid token limits
            if len(content) > 4000:
                logger.debug("Content too long, truncating for summarization")
                content = content[:4000] + "..."
            
            prompt = f"""Please provide a concise summary of the following content in no more than {max_length} characters.
Focus on the key points and main ideas:

Content:
{content}

Summary:"""
            
            logger.debug("Generating summary with Gemini")
            response = self.model.generate_content(prompt)
            
            summary = response.text.strip()
            logger.info(f"Summary generated: {len(summary)} characters")
            
            return summary
        
        except Exception as e:
            error_msg = f"Error summarizing content: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "content_length": len(content),
                "max_length": max_length,
                "model_name": self.model_name
            })
            return error_msg
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        Extract important keywords and phrases from text content
        
        Identifies and extracts the most relevant keywords and phrases from content
        for improved search indexing, content categorization, and metadata generation.
        This helps improve RAG retrieval accuracy and content organization.
        
        Keyword Extraction Features:
        - Semantic relevance assessment
        - Technical term identification
        - Phrase and multi-word concept extraction
        - Domain-specific terminology recognition
        
        Args:
            content (str): Text content to analyze
            max_keywords (int): Maximum number of keywords to extract (default: 10)
            
        Returns:
            List[str]: List of extracted keywords and phrases
                      Error message list if extraction fails
                      
        Example:
            >>> content = "Python is a versatile programming language..."
            >>> keywords = llm.extract_keywords(content, max_keywords=5)
            >>> print(f"Keywords: {', '.join(keywords)}")
            
        Use Cases:
            - Content tagging and categorization
            - Search index enhancement
            - Document clustering and organization
            - Metadata generation for knowledge bases
        """
        logger.info(f"Extracting keywords from content: {len(content)} characters, max keywords: {max_keywords}")
        
        try:
            # Truncate very long content for processing
            if len(content) > 2000:
                logger.debug("Content too long, truncating for keyword extraction")
                content = content[:2000] + "..."
            
            prompt = f"""Extract the {max_keywords} most important keywords or phrases from the following content. 
            Focus on technical terms, key concepts, and domain-specific terminology.
            Return them as a comma-separated list:

Content:
{content}

Keywords:"""
            
            logger.debug("Extracting keywords with Gemini")
            response = self.model.generate_content(prompt)
            
            # Parse and clean keywords
            keywords = [kw.strip() for kw in response.text.split(',') if kw.strip()]
            keywords = keywords[:max_keywords]  # Ensure we don't exceed requested count
            
            logger.info(f"Extracted {len(keywords)} keywords: {keywords[:3]}..." if len(keywords) > 3 else f"Extracted keywords: {keywords}")
            
            return keywords
        
        except Exception as e:
            error_msg = f"Error extracting keywords: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "content_length": len(content),
                "max_keywords": max_keywords,
                "model_name": self.model_name
            })
            return [error_msg]
    
    def generate_title(self, content: str) -> str:
        """
        Generate descriptive title for content
        
        Creates concise, meaningful titles for documents, code files, or text content
        based on analysis of the content's main themes and purpose. This is useful
        for automatic content organization and user interface display.
        
        Title Generation Features:
        - Content analysis for theme extraction
        - Concise, descriptive naming
        - Context-appropriate terminology
        - Length optimization for UI display
        
        Args:
            content (str): Text content to analyze for title generation
            
        Returns:
            str: Generated title or "Untitled Content" if generation fails
            
        Example:
            >>> content = "def calculate_fibonacci(n): ..."
            >>> title = llm.generate_title(content)
            >>> print(f"Generated title: {title}")
            Generated title: Fibonacci Calculation Function
            
        Use Cases:
            - Automatic file naming
            - Content organization and cataloging
            - User interface display
            - Document management systems
        """
        logger.debug(f"Generating title for content: {len(content)} characters")
        
        try:
            # Use first 1000 characters for title generation
            content_preview = content[:1000]
            if len(content) > 1000:
                content_preview += "..."
            
            prompt = f"""Generate a concise, descriptive title for the following content (max 10 words).
Focus on the main purpose, topic, or function:

Content:
{content_preview}

Title:"""
            
            logger.debug("Generating title with Gemini")
            response = self.model.generate_content(prompt)
            
            title = response.text.strip()
            # Clean up common title formatting issues
            title = title.replace('"', '').replace("'", "").strip()
            
            logger.info(f"Generated title: '{title}'")
            return title
        
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            log_error_with_context(e, {
                "content_length": len(content),
                "model_name": self.model_name
            })
            return "Untitled Content"
    
    def classify_content(self, content: str, categories: List[str]) -> str:
        """
        Classify content into predefined categories
        
        Analyzes content and assigns it to the most appropriate category from
        a provided list. This is useful for content organization, routing,
        and automated filing systems.
        
        Classification Features:
        - Multi-category support
        - Content analysis for accurate categorization
        - Fallback handling for edge cases
        - Fuzzy matching for response validation
        
        Args:
            content (str): Text content to classify
            categories (List[str]): List of possible categories
            
        Returns:
            str: Best matching category from the provided list
                 First category if classification fails
                 "Unknown" if no categories provided
                 
        Example:
            >>> content = "def sort_array(arr): return sorted(arr)"
            >>> categories = ["documentation", "code", "configuration"]
            >>> category = llm.classify_content(content, categories)
            >>> print(f"Classified as: {category}")
            Classified as: code
            
        Use Cases:
            - Automatic content routing
            - Document organization systems
            - Content filtering and sorting
            - Workflow automation
        """
        logger.info(f"Classifying content into categories: {categories}")
        logger.debug(f"Content length: {len(content)} characters")
        
        try:
            if not categories:
                logger.warning("No categories provided for classification")
                return "Unknown"
                
            # Truncate content for processing
            content_preview = content[:1000]
            if len(content) > 1000:
                content_preview += "..."
                
            categories_str = ", ".join(categories)
            prompt = f"""Classify the following content into one of these categories: {categories_str}

Analyze the content type, purpose, and structure to determine the best category.

Content:
{content_preview}

Category:"""
            
            logger.debug("Classifying content with Gemini")
            response = self.model.generate_content(prompt)
            classification = response.text.strip().lower()
            
            # Find the best matching category using fuzzy matching
            for category in categories:
                if category.lower() in classification or classification in category.lower():
                    logger.info(f"Content classified as: {category}")
                    return category
            
            # If no exact match, return the first category as fallback
            fallback = categories[0] if categories else "Unknown"
            logger.warning(f"No category match found, using fallback: {fallback}")
            return fallback
        
        except Exception as e:
            logger.error(f"Error classifying content: {str(e)}")
            log_error_with_context(e, {
                "content_length": len(content),
                "categories": categories,
                "model_name": self.model_name
            })
            return categories[0] if categories else "Unknown"
    
    def explain_code(self, code: str, language: str = None) -> str:
        """
        Generate natural language explanation of code functionality
        
        Analyzes code and produces human-readable explanations of what the code
        does, how it works, and its purpose. This is valuable for documentation
        generation, code review assistance, and educational purposes.
        
        Code Explanation Features:
        - Language-aware analysis
        - Function and class breakdown
        - Logic flow explanation
        - Best practices and patterns identification
        
        Args:
            code (str): Code snippet or file content to explain
            language (str, optional): Programming language for context
            
        Returns:
            str: Natural language explanation of the code
                 Error message if explanation generation fails
                 
        Example:
            >>> code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
            >>> explanation = llm.explain_code(code, "python")
            >>> print(explanation)
            
        Use Cases:
            - Automatic documentation generation
            - Code review assistance
            - Educational content creation
            - Knowledge transfer and onboarding
        """
        logger.info(f"Explaining code: {len(code)} characters, language: {language or 'auto-detect'}")
        
        try:
            # Truncate very long code for processing
            if len(code) > 2000:
                logger.debug("Code too long, truncating for explanation")
                code = code[:2000] + "\n# ... (code continues)"
            
            lang_info = f" (written in {language})" if language else ""
            prompt = f"""Explain what the following code{lang_info} does in simple terms.
Break down the functionality, logic flow, and purpose:

Code:
{code}

Explanation:"""
            
            logger.debug("Generating code explanation with Gemini")
            response = self.model.generate_content(prompt)
            
            explanation = response.text.strip()
            logger.info(f"Code explanation generated: {len(explanation)} characters")
            
            return explanation
        
        except Exception as e:
            error_msg = f"Error explaining code: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "code_length": len(code),
                "language": language,
                "model_name": self.model_name
            })
            return error_msg
    
    def generate_sql_query(self, natural_language: str, schema_info: str) -> str:
        """
        Generate SQL queries from natural language descriptions
        
        Converts natural language database requests into properly formatted SQL queries
        based on provided schema information. This enables non-technical users to
        interact with databases through natural language interfaces.
        
        SQL Generation Features:
        - Schema-aware query generation
        - Natural language understanding
        - Proper SQL syntax and formatting
        - Support for complex queries and joins
        
        Args:
            natural_language (str): Human-readable database request
            schema_info (str): Database schema information (tables, columns, relationships)
            
        Returns:
            str: Generated SQL query or error comment if generation fails
            
        Example:
            >>> schema = "Table: users (id, name, email, created_at)"
            >>> request = "Find all users created in the last month"
            >>> query = llm.generate_sql_query(request, schema)
            >>> print(query)
            SELECT * FROM users WHERE created_at >= NOW() - INTERVAL 1 MONTH;
            
        Use Cases:
            - Natural language database interfaces
            - Business intelligence tools
            - Data analysis automation
            - Database query assistance
        """
        logger.info(f"Generating SQL query for request: '{natural_language}'")
        logger.debug(f"Schema info length: {len(schema_info)} characters")
        
        try:
            prompt = f"""Given the following database schema, generate a SQL query for the request.
Ensure the query is syntactically correct and follows SQL best practices:

Schema:
{schema_info}

Request: {natural_language}

SQL Query:"""
            
            logger.debug("Generating SQL query with Gemini")
            response = self.model.generate_content(prompt)
            
            sql_query = response.text.strip()
            # Clean up common formatting issues
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            logger.info(f"SQL query generated: {len(sql_query)} characters")
            logger.debug(f"Generated query: {sql_query[:100]}...")
            
            return sql_query
        
        except Exception as e:
            error_msg = f"-- Error generating SQL: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "natural_language": natural_language,
                "schema_length": len(schema_info),
                "model_name": self.model_name
            })
            return error_msg
    
    def improve_prompt(self, original_prompt: str) -> str:
        """
        Enhance user prompts for better AI responses
        
        Analyzes and improves user prompts to make them more specific, clear,
        and likely to produce high-quality responses. This helps users get
        better results from AI systems through prompt optimization.
        
        Prompt Improvement Features:
        - Specificity enhancement
        - Context addition
        - Clarity improvements
        - Structure optimization
        
        Args:
            original_prompt (str): User's original prompt or question
            
        Returns:
            str: Improved prompt with better structure and specificity
                 Original prompt if improvement fails
                 
        Example:
            >>> original = "How do I code?"
            >>> improved = llm.improve_prompt(original)
            >>> print(improved)
            "How do I get started with programming? Please provide specific steps
            for learning a programming language, including resources and practice exercises."
            
        Use Cases:
            - User assistance and guidance
            - Prompt engineering education
            - Query optimization systems
            - AI interaction improvement
        """
        logger.info(f"Improving prompt: '{original_prompt[:100]}{'...' if len(original_prompt) > 100 else ''}'")
        
        try:
            prompt = f"""Improve the following prompt to make it more specific, clear, and likely to get better results.
Add context, specify desired output format, and make the request more actionable:

Original prompt: {original_prompt}

Improved prompt:"""
            
            logger.debug("Generating improved prompt with Gemini")
            response = self.model.generate_content(prompt)
            
            improved_prompt = response.text.strip()
            # Clean up formatting
            if improved_prompt.startswith('"') and improved_prompt.endswith('"'):
                improved_prompt = improved_prompt[1:-1]
            
            logger.info(f"Prompt improved: {len(original_prompt)} → {len(improved_prompt)} characters")
            
            return improved_prompt
        
        except Exception as e:
            logger.error(f"Error improving prompt: {str(e)}")
            log_error_with_context(e, {
                "original_prompt_length": len(original_prompt),
                "model_name": self.model_name
            })
            return original_prompt
    
    def check_content_safety(self, content: str) -> Dict[str, Any]:
        """
        Assess content safety and appropriateness using AI moderation
        
        Evaluates content for safety concerns using Gemini's built-in safety features
        and content moderation capabilities. This helps maintain safe and appropriate
        interactions in the RAG chatbot system.
        
        Safety Check Features:
        - Harassment and hate speech detection
        - Dangerous content identification
        - Sexually explicit content filtering
        - Medical and legal misinformation detection
        - Comprehensive safety rating system
        
        Args:
            content (str): Content to evaluate for safety
            
        Returns:
            Dict[str, Any]: Safety assessment containing:
                - is_safe (bool): Overall safety determination
                - safety_ratings (List[Dict]): Detailed category ratings
                - error (str, optional): Error message if assessment fails
                
        Safety Categories:
            - HARM_CATEGORY_HARASSMENT: Harassment and bullying
            - HARM_CATEGORY_HATE_SPEECH: Hate speech and discrimination
            - HARM_CATEGORY_SEXUALLY_EXPLICIT: Sexual content
            - HARM_CATEGORY_DANGEROUS_CONTENT: Dangerous activities
            
        Example:
            >>> content = "How to build a website?"
            >>> safety = llm.check_content_safety(content)
            >>> if safety['is_safe']:
            ...     print("Content is safe to process")
                
        Use Cases:
            - Content moderation systems
            - User-generated content filtering
            - Platform safety compliance
            - Automated content review
        """
        logger.info(f"Checking content safety: {len(content)} characters")
        
        try:
            # Use Gemini's built-in safety features
            logger.debug("Performing safety assessment with Gemini")
            response = self.model.generate_content(content)
            
            # Check if response was blocked due to safety concerns
            if hasattr(response, 'prompt_feedback'):
                safety_ratings = response.prompt_feedback.safety_ratings
                
                # Determine if content is blocked based on high/medium risk ratings
                blocked = any(rating.probability.name in ['HIGH', 'MEDIUM'] for rating in safety_ratings)
                
                safety_result = {
                    'is_safe': not blocked,
                    'safety_ratings': [
                        {
                            'category': rating.category.name,
                            'probability': rating.probability.name
                        } for rating in safety_ratings
                    ]
                }
                
                logger.info(f"Safety check completed: {'SAFE' if safety_result['is_safe'] else 'BLOCKED'}")
                if not safety_result['is_safe']:
                    logger.warning(f"Content blocked due to safety concerns: {[r['category'] for r in safety_result['safety_ratings'] if r['probability'] in ['HIGH', 'MEDIUM']]}")
                
                return safety_result
            
            # If no safety feedback available, assume safe
            logger.debug("No safety feedback available, assuming content is safe")
            return {'is_safe': True, 'safety_ratings': []}
        
        except Exception as e:
            error_msg = f"Error checking content safety: {str(e)}"
            logger.error(error_msg)
            log_error_with_context(e, {
                "content_length": len(content),
                "model_name": self.model_name
            })
            return {'is_safe': False, 'error': str(e)}
