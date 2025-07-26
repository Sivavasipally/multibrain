#!/usr/bin/env python3
"""
Check database schema and fix any missing columns
"""

from app_local import app, db, Context
import sqlite3

def check_database_schema():
    """Check the current database schema"""
    print("🔍 Checking database schema...")
    
    with app.app_context():
        try:
            # Get database file path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            print(f"Database path: {db_path}")
            
            # Connect to SQLite database directly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table schema for contexts
            cursor.execute("PRAGMA table_info(contexts)")
            columns = cursor.fetchall()
            
            print("\n📊 Current 'contexts' table schema:")
            print("Column Name | Type | Not Null | Default | Primary Key")
            print("-" * 60)
            
            column_names = []
            for col in columns:
                column_names.append(col[1])
                print(f"{col[1]:<15} | {col[2]:<8} | {col[3]:<8} | {col[4] or 'None':<7} | {col[5]}")
            
            # Check for missing columns
            required_columns = ['chunk_strategy', 'embedding_model']
            missing_columns = []
            
            for col in required_columns:
                if col not in column_names:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
                return False, missing_columns
            else:
                print(f"\n✅ All required columns present")
                return True, []
                
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            return False, []
        finally:
            if 'conn' in locals():
                conn.close()

def add_missing_columns():
    """Add missing columns to the database"""
    print("\n🔧 Adding missing columns...")
    
    with app.app_context():
        try:
            # Get database file path
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Connect to SQLite database directly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Add missing columns
            try:
                cursor.execute("ALTER TABLE contexts ADD COLUMN chunk_strategy VARCHAR(50) DEFAULT 'language-specific'")
                print("✅ Added chunk_strategy column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("⚠️  chunk_strategy column already exists")
                else:
                    print(f"❌ Error adding chunk_strategy: {e}")
            
            try:
                cursor.execute("ALTER TABLE contexts ADD COLUMN embedding_model VARCHAR(100) DEFAULT 'text-embedding-004'")
                print("✅ Added embedding_model column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("⚠️  embedding_model column already exists")
                else:
                    print(f"❌ Error adding embedding_model: {e}")
            
            conn.commit()
            print("✅ Database schema updated")
            return True
            
        except Exception as e:
            print(f"❌ Error updating schema: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

def recreate_database():
    """Recreate the database with the correct schema"""
    print("\n🔄 Recreating database with correct schema...")
    
    with app.app_context():
        try:
            # Drop all tables and recreate
            db.drop_all()
            db.create_all()
            print("✅ Database recreated with correct schema")
            return True
        except Exception as e:
            print(f"❌ Error recreating database: {e}")
            return False

def test_context_creation():
    """Test context creation after schema fix"""
    print("\n🧪 Testing context creation...")
    
    with app.app_context():
        try:
            # Try to create a context with the new fields
            context = Context(
                name='Test Context',
                description='Test',
                source_type='files',
                chunk_strategy='language-specific',
                embedding_model='text-embedding-004',
                user_id=1,
                status='pending'
            )
            
            db.session.add(context)
            db.session.commit()
            
            print("✅ Context creation successful")
            
            # Clean up
            db.session.delete(context)
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Context creation failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Database Schema Check and Fix")
    print("=" * 50)
    
    # Check current schema
    schema_ok, missing = check_database_schema()
    
    if not schema_ok:
        print(f"\n🔧 Attempting to fix missing columns: {missing}")
        
        # Try to add missing columns
        if add_missing_columns():
            print("\n✅ Schema updated successfully")
        else:
            print("\n⚠️  Column addition failed, trying database recreation...")
            if recreate_database():
                print("✅ Database recreated successfully")
            else:
                print("❌ Database recreation failed")
                exit(1)
    
    # Test context creation
    if test_context_creation():
        print("\n🎉 Database is ready! Context creation should work now.")
    else:
        print("\n❌ Context creation still failing. Manual intervention needed.")
    
    print("\n📋 Next steps:")
    print("1. Restart the Flask server")
    print("2. Try creating a context in the web interface")
    print("3. Check that chunk_strategy and embedding_model are saved correctly")
