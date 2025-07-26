#!/usr/bin/env python3
"""
Test the context creation fix by directly testing the API
"""

import requests
import json

def test_context_creation_fix():
    """Test that context creation now saves the correct values"""
    base_url = "http://localhost:5000/api"
    
    print("🧪 Testing Context Creation Fix")
    print("=" * 50)
    
    # Test data with specific values
    test_data = {
        "name": "Fix Test Context",
        "description": "Testing the chunk strategy and embedding model fix",
        "source_type": "files",
        "chunk_strategy": "language-specific",
        "embedding_model": "text-embedding-004",
        "config": {
            "test_key": "test_value"
        }
    }
    
    try:
        # First register a user
        register_data = {
            "username": "fixtest",
            "email": "fixtest@example.com", 
            "password": "testpass123"
        }
        
        register_response = requests.post(f"{base_url}/auth/register", json=register_data)
        if register_response.status_code == 201:
            print("✅ Test user registered")
        else:
            print(f"⚠️  User registration: {register_response.status_code}")
        
        # Login
        login_data = {
            "username": "fixtest",
            "password": "testpass123"
        }
        
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Create context
        print(f"\n📤 Sending context creation request:")
        print(f"  Chunk Strategy: {test_data['chunk_strategy']}")
        print(f"  Embedding Model: {test_data['embedding_model']}")
        
        context_response = requests.post(f"{base_url}/contexts", json=test_data, headers=headers)
        print(f"\n📥 Response Status: {context_response.status_code}")
        
        if context_response.status_code == 201:
            context = context_response.json()["context"]
            print("✅ Context created successfully!")
            
            print(f"\n📊 Context Response:")
            print(f"  ID: {context['id']}")
            print(f"  Name: {context['name']}")
            print(f"  Chunk Strategy: {context.get('chunk_strategy', 'NOT SET')}")
            print(f"  Embedding Model: {context.get('embedding_model', 'NOT SET')}")
            print(f"  Config: {context.get('config', 'NOT SET')}")
            
            # Verify the values are correct
            success = True
            if context.get('chunk_strategy') == 'language-specific':
                print("✅ Chunk strategy is correct!")
            else:
                print(f"❌ Chunk strategy wrong: expected 'language-specific', got '{context.get('chunk_strategy')}'")
                success = False
            
            if context.get('embedding_model') == 'text-embedding-004':
                print("✅ Embedding model is correct!")
            else:
                print(f"❌ Embedding model wrong: expected 'text-embedding-004', got '{context.get('embedding_model')}'")
                success = False
            
            # Test getting context details
            print(f"\n🔍 Testing context details retrieval...")
            detail_response = requests.get(f"{base_url}/contexts/{context['id']}", headers=headers)
            if detail_response.status_code == 200:
                detail_context = detail_response.json()["context"]
                print(f"📋 Context Details:")
                print(f"  Chunk Strategy: {detail_context.get('chunk_strategy', 'NOT SET')}")
                print(f"  Embedding Model: {detail_context.get('embedding_model', 'NOT SET')}")
                print(f"  Config: {detail_context.get('config', 'NOT SET')}")
                
                if detail_context.get('chunk_strategy') == 'language-specific' and detail_context.get('embedding_model') == 'text-embedding-004':
                    print("✅ Context details are correct!")
                else:
                    print("❌ Context details are incorrect!")
                    success = False
            else:
                print(f"❌ Failed to get context details: {detail_response.status_code}")
                success = False
            
            # Clean up
            delete_response = requests.delete(f"{base_url}/contexts/{context['id']}", headers=headers)
            if delete_response.status_code == 200:
                print("✅ Test context cleaned up")
            
            return success
            
        else:
            print(f"❌ Context creation failed: {context_response.status_code}")
            print(f"Response: {context_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_context_creation_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CONTEXT CREATION FIX SUCCESSFUL!")
        print("✅ Chunk strategy and embedding model are now saved correctly")
        print("✅ The Configuration tab should now show the correct values")
    else:
        print("❌ Context creation fix failed")
        print("The issue still needs to be resolved")
    
    print("\n📋 Next Steps:")
    print("1. If successful: Test in the web interface")
    print("2. Create a context and check the Configuration tab")
    print("3. Verify chunk strategy shows 'Language-Specific'")
    print("4. Verify embedding model shows 'text-embedding-004'")
