#!/usr/bin/env python3
"""
Initialize the database with correct schema
"""

from app_local import app, db
import os

def init_database():
    """Initialize database with all tables"""
    print("🔧 Initializing database...")
    
    with app.app_context():
        try:
            # Drop all existing tables
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating new tables...")
            db.create_all()
            
            # Verify tables were created (including versioning tables)
            from models import User, Context, Document, ChatSession, Message, TextChunk
            from context_versioning import ContextVersion, ContextVersionDiff, VersionTag
            
            # Test that we can create a simple context
            print("Testing Context model...")
            test_user = User(
                username='testuser',
                email='test@example.com'
            )
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
            
            test_context = Context(
                name='Test Context',
                description='Test',
                source_type='files',
                chunk_strategy='language-specific',
                embedding_model='text-embedding-004',
                user_id=test_user.id,
                status='pending'
            )
            test_context.set_config({'test': 'value'})
            
            db.session.add(test_context)
            db.session.commit()
            
            # Verify the context was saved correctly
            saved_context = Context.query.get(test_context.id)
            context_dict = saved_context.to_dict()
            
            print(f"✅ Context created successfully!")
            print(f"  ID: {context_dict['id']}")
            print(f"  Chunk Strategy: {context_dict['chunk_strategy']}")
            print(f"  Embedding Model: {context_dict['embedding_model']}")
            print(f"  Config: {context_dict['config']}")
            
            # Clean up test data
            db.session.delete(test_context)
            db.session.delete(test_user)
            db.session.commit()
            
            print("✅ Database initialized successfully!")
            print("✅ All models working correctly!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎉 Database is ready!")
        print("You can now start the Flask server with: python app_local.py")
    else:
        print("\n❌ Database initialization failed!")
