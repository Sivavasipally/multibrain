"""
Complete database schema reset script for RAG Chatbot PWA
Drops all tables and recreates them with the latest schema
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app_local import app, db
from werkzeug.security import generate_password_hash

def backup_database():
    """Create a backup of the current database"""
    possible_db_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db",
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    db_path = None
    for path in possible_db_paths:
        if path.exists():
            db_path = path
            break
    
    if db_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.parent / f"ragchatbot_backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        print(f"📦 Database backed up to: {backup_path}")
        return backup_path
    else:
        print("ℹ️  No existing database found to backup")
        return None

def drop_database():
    """Drop the existing database file"""
    possible_db_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db",
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    dropped_files = []
    for path in possible_db_paths:
        if path.exists():
            path.unlink()
            dropped_files.append(str(path))
            print(f"🗑️  Dropped database: {path}")
    
    return dropped_files

def create_fresh_schema():
    """Create fresh database schema with all tables"""
    with app.app_context():
        print("🔨 Creating fresh database schema...")
        
        # Create all tables
        db.create_all()
        
        print("✅ Created all database tables:")
        
        # Get table names using inspector
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"  📋 Table: {table}")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"    - {col['name']}: {col['type']} {nullable}{default}")
            print()
        
        return tables

def create_sample_data():
    """Create sample users and data for testing"""
    from models import User, Context, ChatSession
    
    print("👥 Creating sample data...")
    
    try:
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@ragchatbot.local',
            is_active=True,
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create regular test user
        test_user = User(
            username='testuser',
            email='test@ragchatbot.local',
            is_active=True,
            is_admin=False
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        
        # Create demo user
        demo_user = User(
            username='demo',
            email='demo@ragchatbot.local',
            is_active=True,
            is_admin=False
        )
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        
        db.session.commit()
        
        print("✅ Created sample users:")
        print("  👤 admin / admin123 (Admin)")
        print("  👤 testuser / test123 (Regular User)")
        print("  👤 demo / demo123 (Regular User)")
        
        # Create sample context for demo user
        sample_context = Context(
            name='Demo Knowledge Base',
            description='A sample context for demonstration purposes',
            user_id=demo_user.id,
            source_type='files',
            status='ready',
            chunk_strategy='language-specific',
            embedding_model='text-embedding-004',
            total_chunks=0,
            total_tokens=0
        )
        sample_context.set_config({
            'file_paths': [],
            'supported_extensions': ['.txt', '.md', '.pdf', '.docx']
        })
        
        db.session.add(sample_context)
        
        # Create sample chat session
        sample_session = ChatSession(
            user_id=demo_user.id,
            title='Welcome Chat',
        )
        
        db.session.add(sample_session)
        db.session.commit()
        
        print("✅ Created sample context and chat session for demo user")
        
    except Exception as e:
        print(f"⚠️  Error creating sample data: {e}")
        db.session.rollback()

def verify_schema():
    """Verify the schema was created correctly"""
    with app.app_context():
        from sqlalchemy import inspect, text
        
        print("🔍 Verifying database schema...")
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['users', 'contexts', 'documents', 'text_chunks', 'chat_sessions', 'messages']
        
        print(f"📊 Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  ✅ {table}")
        
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Verify users table has is_admin column
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'is_admin' not in users_columns:
            print("❌ Missing is_admin column in users table")
            return False
        
        print("✅ All expected tables and columns found")
        
        # Test database connectivity
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.fetchone()[0]
                print(f"👥 Database connectivity test passed - {user_count} users found")
        except Exception as e:
            print(f"❌ Database connectivity test failed: {e}")
            return False
        
        return True

def main():
    """Main reset function"""
    print("🚀 RAG Chatbot Database Schema Reset Tool")
    print("=" * 60)
    
    # Show current status
    print("📊 Current Status:")
    possible_db_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db", 
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    existing_db = None
    for path in possible_db_paths:
        if path.exists():
            existing_db = path
            size = path.stat().st_size
            print(f"  📁 Found existing database: {path} ({size:,} bytes)")
            break
    
    if not existing_db:
        print("  ℹ️  No existing database found")
    
    # Confirm action
    print("\n⚠️  WARNING: This will completely reset your database!")
    print("   - All existing data will be lost")
    print("   - A backup will be created automatically")
    print("   - Fresh schema will be created")
    print("   - Sample data will be added")
    
    confirm = input("\n❓ Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return False
    
    print("\n🔄 Starting database reset...")
    
    # Step 1: Backup existing database
    backup_path = backup_database()
    
    # Step 2: Drop existing database
    dropped_files = drop_database()
    
    # Step 3: Create fresh schema
    try:
        tables = create_fresh_schema()
        print(f"✅ Successfully created {len(tables)} tables")
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        return False
    
    # Step 4: Create sample data
    try:
        create_sample_data()
    except Exception as e:
        print(f"⚠️  Warning: Could not create sample data: {e}")
    
    # Step 5: Verify schema
    if verify_schema():
        print("\n🎉 Database schema reset completed successfully!")
        
        if backup_path:
            print(f"📦 Original database backed up to: {backup_path}")
        
        print("\n🚀 You can now start your RAG Chatbot application")
        print("\n👤 Sample login credentials:")
        print("  Admin:     admin / admin123")
        print("  Test User: testuser / test123") 
        print("  Demo User: demo / demo123")
        
        return True
    else:
        print("\n❌ Schema verification failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)