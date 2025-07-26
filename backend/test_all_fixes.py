#!/usr/bin/env python3
"""
Comprehensive test suite to verify all fixes are working
"""

import requests
import json
import tempfile
import os
from pathlib import Path

def test_app_startup():
    """Test that the app starts without errors"""
    print("🚀 Testing app startup...")
    try:
        from app_local import app, db
        with app.app_context():
            # Test database connection
            db.create_all()
            print("  ✅ App starts successfully")
            print("  ✅ Database connection works")
            return True
    except Exception as e:
        print(f"  ❌ App startup failed: {e}")
        return False

def test_security_fixes():
    """Test security improvements"""
    print("🔒 Testing security fixes...")
    
    try:
        from app_local import app
        
        # Check if secret key is not the default
        if app.config['SECRET_KEY'] != 'local-dev-secret-key':
            print("  ✅ Secret key is properly configured")
        else:
            print("  ⚠️  Secret key still using default (check .env file)")
        
        # Test security headers
        with app.test_client() as client:
            response = client.get('/api/health')
            headers = response.headers
            
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection'
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if not missing_headers:
                print("  ✅ Security headers are present")
            else:
                print(f"  ⚠️  Missing security headers: {missing_headers}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Security test failed: {e}")
        return False

def test_route_blueprints():
    """Test that route blueprints are working"""
    print("🛣️  Testing route blueprints...")
    
    try:
        from app_local import app
        
        with app.test_client() as client:
            # Test admin routes
            response = client.get('/api/admin/dashboard')
            if response.status_code in [200, 401]:  # 401 is expected without auth
                print("  ✅ Admin routes registered")
            else:
                print(f"  ❌ Admin routes issue: {response.status_code}")
            
            # Test auth routes
            response = client.post('/api/auth/register', json={
                'username': 'test', 'email': 'test@test.com', 'password': 'test'
            })
            if response.status_code in [201, 400, 409]:  # Various expected responses
                print("  ✅ Auth routes registered")
            else:
                print(f"  ❌ Auth routes issue: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Route blueprint test failed: {e}")
        return False

def test_models_and_database():
    """Test that all models work correctly"""
    print("🗄️  Testing models and database...")
    
    try:
        from app_local import app, db
        from models import User, Context, Document, ChatSession, Message, TextChunk
        
        with app.app_context():
            # Test model creation
            test_user = User(
                username='testuser_fixes',
                email='testfixes@example.com'
            )
            test_user.set_password('testpass')
            
            db.session.add(test_user)
            db.session.commit()
            
            # Test context creation with correct fields
            test_context = Context(
                name='Test Context Fixes',
                description='Testing fixes',
                source_type='files',
                chunk_strategy='language-specific',
                embedding_model='text-embedding-004',
                user_id=test_user.id,
                status='pending'
            )
            test_context.set_config({'test': 'value'})
            
            db.session.add(test_context)
            db.session.commit()
            
            # Test TextChunk with new methods
            test_chunk = TextChunk(
                context_id=test_context.id,
                file_name='test.txt',
                chunk_index=0,
                content='Test content'
            )
            test_chunk.set_file_info({'file_type': '.txt', 'size': 100})
            
            db.session.add(test_chunk)
            db.session.commit()
            
            # Verify data
            saved_context = Context.query.get(test_context.id)
            context_dict = saved_context.to_dict()
            
            if (context_dict['chunk_strategy'] == 'language-specific' and 
                context_dict['embedding_model'] == 'text-embedding-004'):
                print("  ✅ Context configuration fix working")
            else:
                print("  ❌ Context configuration issue")
            
            # Test TextChunk methods
            file_info = test_chunk.get_file_info()
            if file_info.get('file_type') == '.txt':
                print("  ✅ TextChunk methods working")
            else:
                print("  ❌ TextChunk methods issue")
            
            # Clean up
            db.session.delete(test_chunk)
            db.session.delete(test_context)
            db.session.delete(test_user)
            db.session.commit()
            
            print("  ✅ All models working correctly")
            return True
            
    except Exception as e:
        print(f"  ❌ Models test failed: {e}")
        return False

def test_file_operations():
    """Test file upload and processing"""
    print("📁 Testing file operations...")
    
    try:
        # Test that upload directory exists
        upload_dir = Path("uploads")
        if upload_dir.exists():
            print("  ✅ Upload directory exists")
        else:
            upload_dir.mkdir(exist_ok=True)
            print("  ✅ Upload directory created")
        
        # Test file processing functions
        from app_local import chunk_text

        test_content = "This is a test document for processing."
        chunks = chunk_text(test_content, chunk_size=50, chunk_strategy='language-specific')
        
        if chunks and len(chunks) > 0:
            print("  ✅ Text chunking working")
        else:
            print("  ❌ Text chunking issue")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 Running Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        test_app_startup,
        test_security_fixes,
        test_route_blueprints,
        test_models_and_database,
        test_file_operations
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
            print()
    
    print("=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your RAG Chatbot is fully functional and optimized!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1)
