#!/usr/bin/env python3
"""
Simple test for context creation using the API
"""

import requests
import json

def test_context_creation_api():
    """Test context creation via API"""
    base_url = "http://localhost:5000/api"
    
    print("🧪 Testing context creation via API...")
    
    # First, try to register a test user
    register_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123"
    }
    
    try:
        register_response = requests.post(f"{base_url}/auth/register", json=register_data)
        if register_response.status_code == 201:
            print("✅ Test user registered")
        else:
            print(f"⚠️  User registration: {register_response.status_code}")
    except Exception as e:
        print(f"⚠️  Registration error: {e}")
    
    # Login to get token
    login_data = {
        "username": "testuser2",
        "password": "testpass123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Create context with specific configuration
    headers = {"Authorization": f"Bearer {token}"}
    context_data = {
        "name": "Test Context API",
        "description": "Testing context creation via API",
        "source_type": "files",
        "chunk_strategy": "language-specific",
        "embedding_model": "text-embedding-004",
        "config": {
            "test_setting": "test_value"
        }
    }
    
    try:
        context_response = requests.post(f"{base_url}/contexts", json=context_data, headers=headers)
        print(f"Context creation status: {context_response.status_code}")
        
        if context_response.status_code == 201:
            context = context_response.json()["context"]
            print("✅ Context created successfully!")
            print(f"  ID: {context['id']}")
            print(f"  Name: {context['name']}")
            print(f"  Chunk Strategy: {context.get('chunk_strategy', 'NOT SET')}")
            print(f"  Embedding Model: {context.get('embedding_model', 'NOT SET')}")
            print(f"  Config: {context.get('config', 'NOT SET')}")
            
            # Test getting the context details
            detail_response = requests.get(f"{base_url}/contexts/{context['id']}", headers=headers)
            if detail_response.status_code == 200:
                detail_context = detail_response.json()["context"]
                print("\n📋 Context details from GET request:")
                print(f"  Chunk Strategy: {detail_context.get('chunk_strategy', 'NOT SET')}")
                print(f"  Embedding Model: {detail_context.get('embedding_model', 'NOT SET')}")
                print(f"  Config: {detail_context.get('config', 'NOT SET')}")
                
                # Check if the values are correct
                if detail_context.get('chunk_strategy') == 'language-specific':
                    print("✅ Chunk strategy saved correctly")
                else:
                    print(f"❌ Chunk strategy wrong: {detail_context.get('chunk_strategy')}")
                
                if detail_context.get('embedding_model') == 'text-embedding-004':
                    print("✅ Embedding model saved correctly")
                else:
                    print(f"❌ Embedding model wrong: {detail_context.get('embedding_model')}")
            
            # Clean up - delete the test context
            delete_response = requests.delete(f"{base_url}/contexts/{context['id']}", headers=headers)
            if delete_response.status_code == 200:
                print("✅ Test context cleaned up")
            
            return True
        else:
            print(f"❌ Context creation failed: {context_response.status_code}")
            print(f"Response: {context_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Context creation error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 API Context Creation Test")
    print("=" * 50)
    
    success = test_context_creation_api()
    
    if success:
        print("\n🎉 API test passed! Context creation is working.")
    else:
        print("\n❌ API test failed. Check the server logs for details.")
