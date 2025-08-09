"""
Simple SQLite schema viewer that doesn't require Flask
"""

import sqlite3
import os
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

def show_schema():
    """Display database schema using direct SQLite connection"""
    db_path = find_database()
    
    if not db_path:
        print("❌ Database file not found")
        return False
    
    print("📊 RAG Chatbot Database Schema")
    print("=" * 50)
    print(f"📁 Database: {db_path}")
    print(f"📏 Size: {db_path.stat().st_size:,} bytes")
    print()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"📋 Tables found: {len(tables)}")
        print()
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            print(f"📋 Table: {table_name.upper()}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Header
            print(f"{'ID':<3} {'Column':<20} {'Type':<15} {'NotNull':<7} {'Default':<10} {'PK'}")
            print("-" * 65)
            
            for col in columns:
                cid, name, dtype, notnull, default, pk = col
                default_str = str(default) if default is not None else "-"
                pk_str = "Yes" if pk else "-"
                notnull_str = "Yes" if notnull else "No"
                
                print(f"{cid:<3} {name:<20} {dtype:<15} {notnull_str:<7} {default_str:<10} {pk_str}")
            
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"\n📊 Rows: {count:,}")
            except:
                print(f"\n📊 Rows: Unable to count")
            
            # Show sample data for some tables
            if table_name in ['users', 'contexts'] and count > 0:
                print(f"\n🔍 Sample data:")
                try:
                    if table_name == 'users':
                        cursor.execute("SELECT username, email, is_admin FROM users LIMIT 3")
                        rows = cursor.fetchall()
                        for row in rows:
                            admin_status = " (Admin)" if row[2] else ""
                            print(f"   - {row[0]} ({row[1]}){admin_status}")
                    elif table_name == 'contexts':
                        cursor.execute("SELECT name, source_type, status FROM contexts LIMIT 3")
                        rows = cursor.fetchall()
                        for row in rows:
                            print(f"   - {row[0]} ({row[1]}) - {row[2]}")
                except Exception as e:
                    print(f"   Could not fetch sample: {e}")
            
            print("\n" + "=" * 50 + "\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return False

if __name__ == "__main__":
    success = show_schema()
    if success:
        print("✅ Schema displayed successfully")
    else:
        print("❌ Failed to display schema")