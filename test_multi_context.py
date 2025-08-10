#!/usr/bin/env python3
"""
Test script to debug multi-context chat processing
"""

import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

from models import Context, db
from services.vector_service import VectorService

def test_multi_context_flow():
    """Test the complete multi-context search flow"""
    try:
        from app_local import app
        
        with app.app_context():
            # Test the actual flow that happens in chat
            contexts = Context.query.all()
            print('Testing chat context processing flow...')
            print(f'Available contexts: {len(contexts)}')
            
            for ctx in contexts:
                print(f'\nContext {ctx.id} ({ctx.name}):')
                print(f'  Vector store: {ctx.vector_store_path}')
                print(f'  Exists: {os.path.exists(ctx.vector_store_path) if ctx.vector_store_path else False}')
                
                if ctx.vector_store_path and os.path.exists(ctx.vector_store_path):
                    # Test searching this context
                    vector_service = VectorService('text-embedding-004')
                    try:
                        # Try with a generic query
                        results = vector_service.search_similar(ctx.vector_store_path, 'what information do you have', top_k=2)
                        print(f'  Search results: {len(results)} chunks')
                        for i, chunk in enumerate(results):
                            content_preview = chunk.get('content', '')[:100].replace('\n', ' ')
                            source = chunk.get('source', 'unknown')
                            score = chunk.get('score', 0)
                            print(f'    {i+1}. [{source}] Score: {score:.3f} - {content_preview}...')
                    except Exception as e:
                        print(f'  Search error: {e}')
            
            # Simulate what happens when user selects multiple contexts
            print('\n=== SIMULATING MULTI-CONTEXT SEARCH ===')
            query = 'give me what all you know about'
            print(f'Query: {query}')
            
            all_chunks = []
            valid_contexts = []
            
            for ctx in contexts:
                if ctx.vector_store_path and os.path.exists(ctx.vector_store_path):
                    valid_contexts.append(ctx.name)
                    print(f'\nSearching in {ctx.name}...')
                    try:
                        vector_service = VectorService('text-embedding-004')
                        chunks = vector_service.search_similar(ctx.vector_store_path, query, top_k=3)
                        print(f'Found {len(chunks)} chunks')
                        all_chunks.extend(chunks)
                        
                        for chunk in chunks:
                            content_preview = chunk.get('content', '')[:80].replace('\n', ' ')
                            print(f'  - {content_preview}...')
                            
                    except Exception as e:
                        print(f'Search failed: {e}')
            
            print(f'\nTOTAL CHUNKS FROM ALL CONTEXTS: {len(all_chunks)}')
            print(f'Valid contexts searched: {valid_contexts}')
            
            if all_chunks:
                print('\n=== CONTEXT PREPARATION TEST ===')
                from services.llm_service import LLMService
                try:
                    llm_service = LLMService()
                    context_text = llm_service._prepare_context(all_chunks)
                    print(f'Prepared context length: {len(context_text)} characters')
                    print('Context preview:')
                    print(context_text[:500] + '...' if len(context_text) > 500 else context_text)
                except Exception as e:
                    print(f'Context preparation error: {e}')
            else:
                print('No chunks found - this explains why chat is not working!')
                
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_multi_context_flow()