#!/usr/bin/env python3
"""
Test script for context creation functionality
"""

from app_local import app, db, Context, User
import json

def test_context_creation():
    """Test context creation with proper configuration"""
    print("🧪 Testing context creation...")
    
    with app.app_context():
        try:
            # Create a test user first
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com'
                )
                test_user.set_password('testpass')
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created")
            
            # Test context creation with specific configuration
            test_data = {
                'name': 'Test Context',
                'description': 'Test context for debugging',
                'source_type': 'files',
                'chunk_strategy': 'language-specific',
                'embedding_model': 'text-embedding-004',
                'config': {
                    'test_key': 'test_value'
                }
            }
            
            # Create context
            context = Context(
                name=test_data['name'],
                description=test_data['description'],
                source_type=test_data['source_type'],
                chunk_strategy=test_data['chunk_strategy'],
                embedding_model=test_data['embedding_model'],
                user_id=test_user.id,
                status='pending'
            )
            
            # Set configuration
            full_config = test_data['config']
            full_config.update({
                'chunk_strategy': test_data['chunk_strategy'],
                'embedding_model': test_data['embedding_model']
            })
            context.set_config(full_config)
            
            db.session.add(context)
            db.session.commit()
            
            print(f"✅ Context created with ID: {context.id}")
            
            # Test retrieval
            retrieved_context = Context.query.get(context.id)
            context_dict = retrieved_context.to_dict()
            
            print(f"📊 Context details:")
            print(f"  Name: {context_dict['name']}")
            print(f"  Chunk Strategy: {context_dict['chunk_strategy']}")
            print(f"  Embedding Model: {context_dict['embedding_model']}")
            print(f"  Config: {context_dict['config']}")
            
            # Verify values
            if context_dict['chunk_strategy'] == 'language-specific':
                print("✅ Chunk strategy correct")
            else:
                print(f"❌ Chunk strategy wrong: expected 'language-specific', got '{context_dict['chunk_strategy']}'")
            
            if context_dict['embedding_model'] == 'text-embedding-004':
                print("✅ Embedding model correct")
            else:
                print(f"❌ Embedding model wrong: expected 'text-embedding-004', got '{context_dict['embedding_model']}'")
            
            # Clean up
            db.session.delete(context)
            db.session.commit()
            print("✅ Test context cleaned up")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False

def test_api_endpoint():
    """Test the API endpoint directly"""
    print("\n🧪 Testing API endpoint...")
    
    with app.test_client() as client:
        try:
            # First login to get a token
            login_response = client.post('/api/auth/login', 
                json={'username': 'testuser', 'password': 'testpass'})
            
            if login_response.status_code != 200:
                print("❌ Login failed")
                return False
            
            token = login_response.json['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test context creation
            context_data = {
                'name': 'API Test Context',
                'description': 'Test context via API',
                'source_type': 'files',
                'chunk_strategy': 'language-specific',
                'embedding_model': 'text-embedding-004',
                'config': {
                    'api_test': True
                }
            }
            
            response = client.post('/api/contexts', 
                json=context_data, 
                headers=headers)
            
            if response.status_code == 201:
                context = response.json['context']
                print(f"✅ API context created with ID: {context['id']}")
                print(f"  Chunk Strategy: {context['chunk_strategy']}")
                print(f"  Embedding Model: {context['embedding_model']}")
                print(f"  Config: {context['config']}")
                
                # Clean up
                delete_response = client.delete(f'/api/contexts/{context["id"]}', 
                    headers=headers)
                if delete_response.status_code == 200:
                    print("✅ API test context cleaned up")
                
                return True
            else:
                print(f"❌ API context creation failed: {response.status_code}")
                print(f"Response: {response.json}")
                return False
                
        except Exception as e:
            print(f"❌ API test error: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Context Creation Tests")
    print("=" * 50)
    
    success1 = test_context_creation()
    success2 = test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"✅ Direct creation: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ API endpoint: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Context creation is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
