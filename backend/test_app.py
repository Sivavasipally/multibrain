#!/usr/bin/env python3
"""
Test script for the RAG Chatbot application
"""

import sys
import os

def test_imports():
    """Test if all imports work"""
    print("🧪 Testing imports...")
    
    try:
        from app_local import app, db
        print("✅ App imports successful")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n🧪 Testing health endpoint...")
    
    try:
        from app_local import app
        
        with app.test_client() as client:
            response = client.get('/api/health')
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.get_json()}")
            
            if response.status_code == 200:
                print("✅ Health endpoint working")
                return True
            else:
                print("❌ Health endpoint failed")
                return False
                
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\n🧪 Testing database...")
    
    try:
        from app_local import app, db
        
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✅ Database tables created")
            
            # Test a simple query
            from app_local import User
            user_count = User.query.count()
            print(f"✅ Database query successful (users: {user_count})")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_admin_routes():
    """Test admin routes"""
    print("\n🧪 Testing admin routes...")
    
    try:
        from app_local import app
        
        with app.test_client() as client:
            # Test admin dashboard (should require auth)
            response = client.get('/api/admin/dashboard')
            print(f"Admin dashboard status: {response.status_code}")
            
            if response.status_code in [401, 403]:  # Unauthorized/Forbidden is expected
                print("✅ Admin routes registered (auth required)")
                return True
            else:
                print(f"⚠️  Unexpected admin response: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Admin routes test failed: {e}")
        return False

def test_dependencies():
    """Test optional dependencies"""
    print("\n🧪 Testing dependencies...")
    
    dependencies = [
        ('flask', 'Flask'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('requests', 'Requests'),
        ('google.generativeai', 'Google AI'),
        ('openai', 'OpenAI'),
        ('docx', 'python-docx'),
        ('openpyxl', 'OpenPyXL')
    ]
    
    working = 0
    total = len(dependencies)
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}")
            working += 1
        except ImportError:
            print(f"❌ {name}")
    
    print(f"\n📊 Dependencies: {working}/{total} working")
    return working >= total * 0.7  # 70% success rate

def main():
    """Run all tests"""
    print("🚀 RAG Chatbot Application Tests")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Dependencies", test_dependencies),
        ("Database", test_database),
        ("Health Endpoint", test_health_endpoint),
        ("Admin Routes", test_admin_routes)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The application is ready to run.")
        print("\n📋 Next steps:")
        print("1. Run: python app_local.py")
        print("2. Open: http://localhost:5000")
        print("3. Create an account and start using the app!")
    elif passed >= len(results) * 0.8:
        print("⚠️  Most tests passed. The application should work with basic functionality.")
        print("\n📋 You can still run the app, but some features may be limited.")
    else:
        print("❌ Multiple tests failed. Please check the installation.")
        print("\n📋 Try running: python install_with_pip.py")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
