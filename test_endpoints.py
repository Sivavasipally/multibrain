#!/usr/bin/env python3
"""
Quick endpoint test script
"""

import requests
import json

def test_endpoints():
    base_url = "http://localhost:5000"
    
    # Test endpoints that should exist
    endpoints_to_test = [
        ("GET", "/api/health"),
        ("GET", "/api/upload/supported-extensions"),
        ("POST", "/api/auth/register"),
        ("POST", "/api/auth/login"),
        ("GET", "/api/auth/profile"),
        ("POST", "/api/auth/logout"),
        ("POST", "/api/auth/refresh"),
        ("GET", "/api/contexts"),
        ("POST", "/api/contexts"),
        ("GET", "/api/chat/sessions"),
        ("POST", "/api/chat/sessions"),
        ("POST", "/api/chat/query"),
        ("GET", "/api/preferences"),
        ("PUT", "/api/preferences"),
    ]
    
    print("🧪 Testing endpoint availability...")
    print("=" * 60)
    
    available = []
    unavailable = []
    
    for method, endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)
            elif method == "PUT":
                response = requests.put(url, json={}, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, timeout=5)
            
            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                status = "✅ AVAILABLE"
                available.append(f"{method} {endpoint}")
            else:
                status = "❌ NOT FOUND"
                unavailable.append(f"{method} {endpoint}")
                
            print(f"{status:15} {method:6} {endpoint:30} ({response.status_code})")
            
        except requests.exceptions.ConnectionError:
            print(f"{'🔌 SERVER OFF':15} {method:6} {endpoint:30} (Connection refused)")
            break
        except Exception as e:
            print(f"{'⚠️ ERROR':15} {method:6} {endpoint:30} ({str(e)[:20]})")
    
    print("=" * 60)
    print(f"✅ Available: {len(available)}")
    print(f"❌ Missing: {len(unavailable)}")
    
    if unavailable:
        print("\n❌ Missing endpoints:")
        for endpoint in unavailable:
            print(f"   • {endpoint}")

if __name__ == "__main__":
    test_endpoints()