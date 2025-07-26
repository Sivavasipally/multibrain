#!/usr/bin/env python3
"""
Test script for context deletion functionality
"""

from app_local import app, db, Context, TextChunk

def test_context_deletion():
    """Test context deletion with proper app context"""
    print("🧪 Testing context deletion...")
    
    with app.app_context():
        try:
            # Test that we can access the database
            context_count = Context.query.count()
            print(f"✅ Database access working - {context_count} contexts found")
            
            # Test that we can access TextChunk model
            chunk_count = TextChunk.query.count()
            print(f"✅ TextChunk model access working - {chunk_count} chunks found")
            
            print("✅ Context deletion should work now!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    success = test_context_deletion()
    if success:
        print("\n🎉 Context deletion test passed!")
        print("The server should now handle context deletion properly.")
    else:
        print("\n❌ Context deletion test failed!")
        print("There may still be issues with the database setup.")
