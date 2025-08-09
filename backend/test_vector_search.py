#!/usr/bin/env python3
"""
Test vector search with the current context
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_vector_search():
    """Test vector search functionality"""
    print("🔍 Testing Vector Search")
    print("=" * 30)
    
    try:
        # Import required modules
        from services.vector_service import VectorService
        import sqlite3
        
        # Find database
        db_path = backend_dir / "instance" / "ragchatbot.db"
        if not db_path.exists():
            print("❌ Database not found")
            return False
            
        print(f"📁 Using database: {db_path}")
        
        # Get context information
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, vector_store_path, embedding_model FROM contexts WHERE status = 'ready' LIMIT 1")
        context = cursor.fetchone()
        
        if not context:
            print("❌ No ready context found")
            return False
            
        context_id, context_name, vector_store_path, embedding_model = context
        print(f"📋 Testing context: {context_name}")
        print(f"🗂️  Vector store path: {vector_store_path}")
        print(f"🤖 Embedding model: {embedding_model}")
        
        # Initialize vector service
        vector_service = VectorService(embedding_model or 'text-embedding-004')
        
        # Test query
        query = "client connect"
        print(f"\n🔎 Searching for: '{query}'")
        
        try:
            results = vector_service.search_similar(vector_store_path, query, top_k=3)
            print(f"✅ Found {len(results)} results:")
            
            for i, result in enumerate(results, 1):
                content = result.get('content', 'No content')[:100]  # First 100 chars
                score = result.get('score', 0)
                source = result.get('source', 'Unknown')
                print(f"   {i}. Score: {score:.4f} | Source: {source}")
                print(f"      Content: {content}...")
                print()
                
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vector_search()
    if success:
        print("✅ Vector search test completed successfully!")
    else:
        print("❌ Vector search test failed!")
    sys.exit(0 if success else 1)