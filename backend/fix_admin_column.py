"""
Quick fix script to add is_admin column to users table
Run this if you're getting "no such column: users.is_admin" error
"""

import sqlite3
import os
from pathlib import Path

def fix_admin_column():
    """Add is_admin column to users table in SQLite database"""
    # Check common database locations
    possible_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db",
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found in any of these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        print("Please run the app first to create the database.")
        return False
    
    print(f"📍 Found database at: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_admin' in columns:
            print("✅ is_admin column already exists in the database")
            return True
        
        # Add the is_admin column
        print("📝 Adding is_admin column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        
        # Commit the changes
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_admin' in columns:
            print("✅ Successfully added is_admin column to users table")
            print("🔄 You can now restart your application")
            return True
        else:
            print("❌ Failed to add is_admin column")
            return False
            
    except Exception as e:
        print(f"❌ Error adding is_admin column: {e}")
        return False
    finally:
        if conn:
            conn.close()

def show_table_structure():
    """Show current structure of users table"""
    # Check common database locations
    possible_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db",
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("\n📋 Current users table structure:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Column ID | Name         | Type    | NotNull | Default | PK")
        print("-" * 60)
        for column in columns:
            print(f"{column[0]:9} | {column[1]:12} | {column[2]:7} | {column[3]:7} | {column[4]:7} | {column[5]}")
        
    except Exception as e:
        print(f"❌ Error reading table structure: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 RAG Chatbot Database Fix Tool")
    print("=" * 40)
    
    # Show current table structure
    show_table_structure()
    
    # Fix the admin column
    success = fix_admin_column()
    
    if success:
        # Show updated table structure
        show_table_structure()
        print("\n🎉 Database fix completed!")
        print("🚀 You can now restart your RAG Chatbot application")
    else:
        print("\n❌ Database fix failed!")
        print("💡 Alternative solution: Delete ragchatbot.db and restart the app")