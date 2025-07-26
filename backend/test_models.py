#!/usr/bin/env python3
"""
Test models import and database creation
"""

def test_models_import():
    """Test that models can be imported correctly"""
    print("🧪 Testing models import...")
    
    try:
        from models import db, User, Context, Document, ChatSession, Message, TextChunk
        print("✅ All models imported successfully")
        
        # Check model table names
        print(f"User table: {User.__tablename__}")
        print(f"Context table: {Context.__tablename__}")
        print(f"Document table: {Document.__tablename__}")
        print(f"ChatSession table: {ChatSession.__tablename__}")
        print(f"Message table: {Message.__tablename__}")
        print(f"TextChunk table: {TextChunk.__tablename__}")
        
        return True
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False

def test_app_import():
    """Test that app can be imported correctly"""
    print("\n🧪 Testing app import...")
    
    try:
        from app_local import app, db
        print("✅ App imported successfully")
        
        # Check database URI
        with app.app_context():
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            print(f"Database engine: {db.engine}")
            
        return True
    except Exception as e:
        print(f"❌ Error importing app: {e}")
        return False

def test_database_creation():
    """Test database table creation"""
    print("\n🧪 Testing database creation...")
    
    try:
        from app_local import app, db
        from models import User, Context, Document, ChatSession, Message, TextChunk
        
        with app.app_context():
            print("Creating tables...")
            db.create_all()
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables created: {tables}")
            
            # Check specific tables
            required_tables = ['users', 'contexts', 'documents', 'chat_sessions', 'messages', 'text_chunks']
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    print(f"✅ {table} table exists")
                else:
                    print(f"❌ {table} table missing")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"Missing tables: {missing_tables}")
                return False
            else:
                print("✅ All required tables created")
                return True
                
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Model and Database Tests")
    print("=" * 50)
    
    success1 = test_models_import()
    success2 = test_app_import()
    success3 = test_database_creation()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"✅ Models import: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ App import: {'PASS' if success2 else 'FAIL'}")
    print(f"✅ Database creation: {'PASS' if success3 else 'FAIL'}")
    
    if success1 and success2 and success3:
        print("\n🎉 All tests passed! Database is ready.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
