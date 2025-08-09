#!/usr/bin/env python3
"""
Check detailed context information in the database
"""

import sqlite3
from pathlib import Path

def find_database():
    """Find the database file"""
    possible_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db",
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def check_context_details():
    """Check detailed context information"""
    db_path = find_database()
    
    if not db_path:
        print("❌ Database file not found!")
        return
    
    print("📊 Context Details Check")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get context details
        cursor.execute("""
            SELECT id, name, status, progress, total_chunks, total_tokens, vector_store_path, user_id
            FROM contexts 
            ORDER BY id
        """)
        contexts = cursor.fetchall()
        
        if not contexts:
            print("No contexts found")
            return
            
        for ctx in contexts:
            ctx_id, name, status, progress, total_chunks, total_tokens, vector_store_path, user_id = ctx
            print(f"📁 Context {ctx_id}: {name}")
            print(f"   Status: {status}")
            print(f"   Progress: {progress}%")
            print(f"   Chunks: {total_chunks}")
            print(f"   Tokens: {total_tokens}")
            print(f"   Vector Store: {vector_store_path}")
            print(f"   User ID: {user_id}")
            
            # Get documents for this context
            cursor.execute("SELECT filename, file_size, chunks_count FROM documents WHERE context_id = ?", (ctx_id,))
            documents = cursor.fetchall()
            
            print(f"   Documents ({len(documents)}):")
            for doc in documents:
                filename, file_size, chunks_count = doc
                print(f"     - {filename} ({file_size} bytes, {chunks_count} chunks)")
            
            # Get actual text chunks
            cursor.execute("SELECT COUNT(*) FROM text_chunks WHERE context_id = ?", (ctx_id,))
            actual_chunks = cursor.fetchone()[0]
            print(f"   Actual chunks in DB: {actual_chunks}")
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_context_details()