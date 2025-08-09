#!/usr/bin/env python3
"""
Simple test using direct HTTP request to test chat functionality
"""

import requests
import json

def test_chat_query():
    """Test chat query via HTTP API"""
    print("🔍 Testing Chat Query via API")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        # First, login to get a token
        print("1. Logging in...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return False
            
        token = login_response.json().get("access_token")
        print("✅ Login successful")
        
        # Set up headers with token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get available contexts
        print("\n2. Getting contexts...")
        contexts_response = requests.get(f"{base_url}/api/contexts", headers=headers)
        
        if contexts_response.status_code != 200:
            print(f"❌ Failed to get contexts: {contexts_response.status_code}")
            return False
            
        contexts = contexts_response.json()
        print(f"✅ Found {len(contexts)} contexts")
        
        if not contexts:
            print("❌ No contexts available for testing")
            return False
            
        # Use the first ready context
        test_context = None
        for ctx in contexts:
            if ctx.get('status') == 'ready':
                test_context = ctx
                break
                
        if not test_context:
            print("❌ No ready contexts found")
            return False
            
        print(f"📋 Using context: {test_context['name']} (ID: {test_context['id']})")
        
        # Test chat query
        print("\n3. Testing chat query...")
        query_data = {
            "message": "what is client connect",
            "context_ids": [test_context['id']]
        }
        
        chat_response = requests.post(f"{base_url}/api/chat/query", headers=headers, json=query_data)
        
        if chat_response.status_code != 200:
            print(f"❌ Chat query failed: {chat_response.status_code}")
            print(chat_response.text)
            return False
            
        result = chat_response.json()
        response_text = result.get("response", "")
        chunks_found = len(result.get("sources", []))
        
        print(f"✅ Chat query successful")
        print(f"📊 Chunks found: {chunks_found}")
        print(f"💬 Response: {response_text[:200]}...")
        
        if chunks_found == 0:
            print("⚠️  No chunks found - this indicates the vector search issue")
            return False
        else:
            print("✅ Vector search working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_chat_query()
    if success:
        print("\n🎉 Chat functionality test passed!")
    else:
        print("\n❌ Chat functionality test failed!")