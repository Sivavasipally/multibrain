#!/usr/bin/env python3
"""
Test file upload functionality after fixing TextChunk methods
"""

import requests
import json
import tempfile
import os

def test_file_upload_fix():
    """Test that file upload now works without the set_file_info error"""
    base_url = "http://localhost:5000/api"
    
    print("🧪 Testing File Upload Fix")
    print("=" * 50)
    
    try:
        # Register and login
        register_data = {
            "username": "uploadtest",
            "email": "uploadtest@example.com", 
            "password": "testpass123"
        }
        
        register_response = requests.post(f"{base_url}/auth/register", json=register_data)
        if register_response.status_code == 201:
            print("✅ Test user registered")
        else:
            print(f"⚠️  User registration: {register_response.status_code}")
        
        # Login
        login_data = {
            "username": "uploadtest",
            "password": "testpass123"
        }
        
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Create a context first
        context_data = {
            "name": "Upload Test Context",
            "description": "Testing file upload functionality",
            "source_type": "files",
            "chunk_strategy": "language-specific",
            "embedding_model": "text-embedding-004"
        }
        
        context_response = requests.post(f"{base_url}/contexts", json=context_data, headers=headers)
        if context_response.status_code != 201:
            print(f"❌ Context creation failed: {context_response.status_code}")
            return False
        
        context = context_response.json()["context"]
        context_id = context["id"]
        print(f"✅ Context created with ID: {context_id}")
        
        # Create a test file
        test_content = """# Test Document

This is a test document for uploading to the RAG chatbot.

## Section 1
This section contains some sample text that will be processed into chunks.

## Section 2
This section contains more sample text to test the chunking functionality.

The file upload should now work without the 'set_file_info' error.
"""
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # Upload the file
            print(f"📤 Uploading test file...")
            
            with open(temp_file_path, 'rb') as f:
                files = {
                    'files': ('test_document.txt', f, 'text/plain')
                }
                data = {
                    'context_id': context_id
                }
                
                upload_response = requests.post(f"{base_url}/upload/files", 
                                              files=files, 
                                              data=data, 
                                              headers=headers)
            
            print(f"📥 Upload Response Status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                upload_result = upload_response.json()
                print("✅ File upload successful!")
                print(f"  Files processed: {upload_result.get('files_processed', 0)}")
                print(f"  Total chunks: {upload_result.get('total_chunks', 0)}")
                
                # Check if chunks were created
                chunks_response = requests.get(f"{base_url}/contexts/{context_id}/chunks", headers=headers)
                if chunks_response.status_code == 200:
                    chunks_data = chunks_response.json()
                    chunk_count = len(chunks_data.get('chunks', []))
                    print(f"✅ Chunks created: {chunk_count}")
                    
                    if chunk_count > 0:
                        # Check a sample chunk
                        sample_chunk = chunks_data['chunks'][0]
                        print(f"📋 Sample chunk:")
                        print(f"  File: {sample_chunk.get('file_name')}")
                        print(f"  Content length: {len(sample_chunk.get('content', ''))}")
                        print(f"  Metadata: {sample_chunk.get('metadata', {})}")
                        
                        success = True
                    else:
                        print("❌ No chunks were created")
                        success = False
                else:
                    print(f"❌ Failed to get chunks: {chunks_response.status_code}")
                    success = False
                
            else:
                print(f"❌ File upload failed: {upload_response.status_code}")
                print(f"Response: {upload_response.text}")
                success = False
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
        
        # Clean up context
        delete_response = requests.delete(f"{base_url}/contexts/{context_id}", headers=headers)
        if delete_response.status_code == 200:
            print("✅ Test context cleaned up")
        
        return success
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_file_upload_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FILE UPLOAD FIX SUCCESSFUL!")
        print("✅ TextChunk.set_file_info() method is now working")
        print("✅ File upload and processing is functional")
    else:
        print("❌ File upload fix failed")
        print("The issue may still need to be resolved")
    
    print("\n📋 Next Steps:")
    print("1. Try uploading a file in the web interface")
    print("2. Check that the file processes without errors")
    print("3. Verify that chunks are created successfully")
