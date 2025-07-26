#!/usr/bin/env python3
"""
Test script for context cleanup functionality
"""

import os
import sys
import json
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_local import app, db
from models import User, Context, Document, ChatSession, Message
from services.context_cleanup_service import ContextCleanupService


def create_test_data():
    """Create test data for cleanup testing"""
    with app.app_context():
        # Create a test user
        test_user = User(
            username='test_cleanup_user',
            email='test@cleanup.com',
            password_hash='dummy_hash'
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Create a test context
        test_context = Context(
            name='Test Cleanup Context',
            description='Context for testing cleanup functionality',
            user_id=test_user.id,
            source_type='files',
            status='ready',
            total_chunks=5,
            total_tokens=1000,
            vector_store_path='vector_store/test_context_cleanup'
        )
        db.session.add(test_context)
        db.session.commit()
        
        # Create test documents
        test_doc1 = Document(
            context_id=test_context.id,
            filename='test_doc1.txt',
            file_path='uploads/test_doc1.txt',
            file_type='text',
            file_size=1024,
            status='processed'
        )
        
        test_doc2 = Document(
            context_id=test_context.id,
            filename='test_doc2.pdf',
            file_path='uploads/test_doc2.pdf',
            file_type='document',
            file_size=2048,
            status='processed'
        )
        
        db.session.add(test_doc1)
        db.session.add(test_doc2)
        db.session.commit()
        
        # Create test chat session
        test_session = ChatSession(
            user_id=test_user.id,
            title='Test Chat Session'
        )
        db.session.add(test_session)
        db.session.commit()
        
        # Create test messages
        test_message1 = Message(
            session_id=test_session.id,
            role='user',
            content='Test question about the context'
        )
        test_message1.set_context_ids([test_context.id])
        
        test_message2 = Message(
            session_id=test_session.id,
            role='assistant',
            content='Test response from the context'
        )
        test_message2.set_context_ids([test_context.id])
        
        db.session.add(test_message1)
        db.session.add(test_message2)
        db.session.commit()
        
        # Create test files and directories
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('vector_store', exist_ok=True)
        
        # Create dummy files
        with open('uploads/test_doc1.txt', 'w') as f:
            f.write('This is a test document for cleanup testing.')
        
        with open('uploads/test_doc2.pdf', 'w') as f:
            f.write('This is a dummy PDF file for cleanup testing.')
        
        # Create dummy vector store
        os.makedirs('vector_store/test_context_cleanup', exist_ok=True)
        with open('vector_store/test_context_cleanup/index.faiss', 'w') as f:
            f.write('dummy vector index')
        
        with open('vector_store/test_context_cleanup/metadata.json', 'w') as f:
            json.dump({
                'chunks': ['chunk1', 'chunk2', 'chunk3'],
                'embedding_model': 'text-embedding-004',
                'created_at': datetime.now(timezone.utc).isoformat()
            }, f)
        
        print(f"Created test data:")
        print(f"  User ID: {test_user.id}")
        print(f"  Context ID: {test_context.id}")
        print(f"  Documents: {len([test_doc1, test_doc2])}")
        print(f"  Chat Session ID: {test_session.id}")
        print(f"  Messages: {len([test_message1, test_message2])}")
        
        return test_user.id, test_context.id


def test_cleanup(user_id, context_id):
    """Test the cleanup functionality"""
    with app.app_context():
        print(f"\n=== Testing Context Cleanup ===")
        print(f"User ID: {user_id}")
        print(f"Context ID: {context_id}")
        
        # Verify data exists before cleanup
        context = db.session.get(Context, context_id)
        documents = Document.query.filter_by(context_id=context_id).all()
        messages = Message.query.all()
        context_messages = [msg for msg in messages if context_id in msg.get_context_ids()]
        
        print(f"\nBefore cleanup:")
        print(f"  Context exists: {context is not None}")
        print(f"  Documents: {len(documents)}")
        print(f"  Messages referencing context: {len(context_messages)}")
        print(f"  Vector store exists: {os.path.exists('vector_store/test_context_cleanup')}")
        print(f"  Upload files exist: {os.path.exists('uploads/test_doc1.txt')}")
        
        # Perform cleanup
        cleanup_service = ContextCleanupService()
        result = cleanup_service.delete_context_completely(context_id, user_id)
        
        print(f"\n=== Cleanup Result ===")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Message: {result['message']}")
            print(f"Stats: {json.dumps(result['stats'], indent=2)}")
        else:
            print(f"Error: {result['error']}")
            print(f"Stats: {json.dumps(result['stats'], indent=2)}")
        
        # Verify data is cleaned up
        context_after = db.session.get(Context, context_id)
        documents_after = Document.query.filter_by(context_id=context_id).all()
        messages_after = Message.query.all()
        context_messages_after = [msg for msg in messages_after if context_id in msg.get_context_ids()]
        
        print(f"\nAfter cleanup:")
        print(f"  Context exists: {context_after is not None}")
        print(f"  Documents: {len(documents_after)}")
        print(f"  Messages referencing context: {len(context_messages_after)}")
        print(f"  Vector store exists: {os.path.exists('vector_store/test_context_cleanup')}")
        print(f"  Upload files exist: {os.path.exists('uploads/test_doc1.txt')}")
        
        return result


def cleanup_test_data(user_id):
    """Clean up any remaining test data"""
    with app.app_context():
        # Clean up test user and any remaining data
        user = db.session.get(User, user_id)
        if user:
            # Clean up any remaining chat sessions
            sessions = ChatSession.query.filter_by(user_id=user_id).all()
            for session in sessions:
                db.session.delete(session)
            
            # Delete user
            db.session.delete(user)
            db.session.commit()
            print(f"Cleaned up test user {user_id}")
        
        # Clean up any remaining test files
        test_files = ['uploads/test_doc1.txt', 'uploads/test_doc2.pdf']
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed test file: {file_path}")


def main():
    """Main test function"""
    print("=== Context Cleanup Test ===")
    
    try:
        # Create test data
        user_id, context_id = create_test_data()
        
        # Test cleanup
        result = test_cleanup(user_id, context_id)
        
        # Clean up test data
        cleanup_test_data(user_id)
        
        print(f"\n=== Test Complete ===")
        if result['success']:
            print("✅ Cleanup test PASSED")
        else:
            print("❌ Cleanup test FAILED")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
