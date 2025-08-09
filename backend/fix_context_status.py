#!/usr/bin/env python3
"""
Fix the current context status and progress to show correct values
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

def fix_context_status():
    """Fix context status and progress"""
    db_path = find_database()
    
    if not db_path:
        print("❌ Database file not found!")
        return
    
    print("🔧 Fixing Context Status and Progress")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get contexts that need fixing
        cursor.execute("""
            SELECT id, name, status, progress, total_chunks 
            FROM contexts 
            WHERE status = 'ready' AND progress != 100
        """)
        contexts = cursor.fetchall()
        
        if not contexts:
            print("✅ No contexts need fixing")
            return
            
        for ctx in contexts:
            ctx_id, name, status, progress, total_chunks = ctx
            print(f"🔧 Fixing Context {ctx_id}: {name}")
            print(f"   Current: status={status}, progress={progress}%")
            
            # Update progress to 100%
            cursor.execute("UPDATE contexts SET progress = 100 WHERE id = ?", (ctx_id,))
            
            print(f"   Updated: status={status}, progress=100%")
        
        # Also fix document chunks_count
        cursor.execute("""
            UPDATE documents 
            SET chunks_count = (
                SELECT COUNT(*) 
                FROM text_chunks 
                WHERE text_chunks.context_id = documents.context_id 
                AND text_chunks.file_name = documents.filename
            )
            WHERE chunks_count = 0
        """)
        
        updated_docs = cursor.rowcount
        if updated_docs > 0:
            print(f"🔧 Updated {updated_docs} document chunk counts")
        
        conn.commit()
        print("✅ Context status and progress updated successfully!")
        
        # Verify changes
        print("\n📊 Updated Context Details:")
        cursor.execute("""
            SELECT id, name, status, progress, total_chunks, total_tokens
            FROM contexts 
            ORDER BY id
        """)
        contexts = cursor.fetchall()
        
        for ctx in contexts:
            ctx_id, name, status, progress, total_chunks, total_tokens = ctx
            print(f"   Context {ctx_id}: {name} | {status} | {progress}% | {total_chunks} chunks | {total_tokens} tokens")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_context_status()