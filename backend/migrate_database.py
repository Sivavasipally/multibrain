"""
Database migration script for RAG Chatbot PWA
Adds missing columns to existing database
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app_local import app, db
from sqlalchemy import inspect, text

def migrate_database():
    """Add missing columns to existing database"""
    print("🔄 Starting database migration...")
    
    with app.app_context():
        try:
            # Check if is_admin column exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            migrations_applied = []
            
            # Migration 1: Add is_admin column
            if 'is_admin' not in columns:
                print("  📝 Adding is_admin column to users table...")
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
                    conn.commit()
                print("  ✅ Added is_admin column successfully")
                migrations_applied.append("is_admin column")
            else:
                print("  ✅ is_admin column already exists")
            
            # Add more migrations here in the future
            # Example:
            # if 'new_column' not in columns:
            #     print("  📝 Adding new_column to users table...")
            #     with db.engine.connect() as conn:
            #         conn.execute(text('ALTER TABLE users ADD COLUMN new_column VARCHAR(255)'))
            #         conn.commit()
            #     migrations_applied.append("new_column")
            
            if migrations_applied:
                print(f"🎉 Database migration completed! Applied: {', '.join(migrations_applied)}")
            else:
                print("✅ Database is already up to date - no migrations needed")
                
        except Exception as e:
            print(f"❌ Migration error: {e}")
            print("\n💡 Solutions:")
            print("   1. Delete the ragchatbot.db file and restart the app to create a fresh database")
            print("   2. Or manually run this SQL: ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            return False
    
    return True

def backup_database():
    """Create a backup of the current database"""
    db_path = "ragchatbot.db"
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"📦 Database backed up to {backup_path}")
        return backup_path
    return None

def main():
    """Main migration function"""
    print("🚀 RAG Chatbot Database Migration Tool")
    print("=" * 50)
    
    # Check if database exists
    db_path = "ragchatbot.db"
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the app first to create the database.")
        sys.exit(1)
    
    # Create backup
    backup_path = backup_database()
    
    # Run migrations
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        if backup_path:
            print(f"📦 Original database backed up to {backup_path}")
        print("🔄 You can now restart your application.")
    else:
        print("\n❌ Migration failed!")
        if backup_path:
            print(f"🔄 You can restore from backup: {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()