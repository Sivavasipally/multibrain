#!/usr/bin/env python3
"""
Test script for context versioning system

This script tests the integrated versioning system by creating test data
and exercising the versioning APIs to ensure everything works correctly.

Usage:
    python test_versioning.py

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import required modules
from app_local import app, db
from models import User, Context, Document
from context_versioning import ContextVersion, ContextVersionService, VersionTag

def test_versioning_system():
    """Test the complete versioning system"""
    
    print("🧪 Testing Context Versioning System")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Clean up any existing test data
            print("1. Cleaning up existing test data...")
            test_user = User.query.filter_by(username='version_test_user').first()
            if test_user:
                Context.query.filter_by(user_id=test_user.id).delete()
                User.query.filter_by(username='version_test_user').delete()
                db.session.commit()
            
            # Create test user
            print("2. Creating test user...")
            user = User(
                username='version_test_user',
                email='test@versioning.com'
            )
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            print(f"   ✓ Created user: {user.username} (ID: {user.id})")
            
            # Create test context
            print("3. Creating test context...")
            context = Context(
                name='Versioning Test Context',
                description='Test context for versioning system',
                source_type='files',
                user_id=user.id,
                status='ready',
                chunk_strategy='language-specific',
                embedding_model='text-embedding-004'
            )
            context.set_config({'test_setting': 'initial_value'})
            db.session.add(context)
            db.session.commit()
            print(f"   ✓ Created context: {context.name} (ID: {context.id})")
            
            # Test version creation
            print("4. Testing version creation...")
            
            # Create first version
            version1 = ContextVersionService.create_version(
                context=context,
                user_id=user.id,
                description="Initial version",
                version_type='manual'
            )
            print(f"   ✓ Created version {version1.version_number}: {version1.description}")
            print(f"     - ID: {version1.id}")
            print(f"     - Type: {version1.version_type}")
            print(f"     - Hash: {version1.content_hash[:8]}...")
            print(f"     - Is current: {version1.is_current}")
            
            # Create second version with changes
            context.total_chunks = 10
            context.total_tokens = 1000
            db.session.commit()
            
            changes = {
                'document_addition': {
                    'operation': 'added',
                    'description': 'Added test documents',
                    'impact_score': 5,
                    'documents_added': 3,
                    'chunks_created': 10,
                    'tokens_processed': 1000
                }
            }
            
            version2 = ContextVersionService.create_version(
                context=context,
                user_id=user.id,
                description="Added test documents",
                version_type='auto',
                changes=changes,
                force_major=False
            )
            print(f"   ✓ Created version {version2.version_number}: {version2.description}")
            print(f"     - Parent version: {version2.parent_version_id}")
            print(f"     - Impact: {version2.change_impact}")
            
            # Test version tagging
            print("5. Testing version tagging...")
            tag = VersionTag(
                version_id=version2.id,
                tag_name='stable',
                tag_description='Stable release with documents',
                tag_type='milestone',
                tag_color='#28a745',
                created_by=user.id
            )
            db.session.add(tag)
            db.session.commit()
            print(f"   ✓ Added tag: {tag.tag_name} to version {version2.version_number}")
            
            # Test version comparison
            print("6. Testing version comparison...")
            comparison = ContextVersionService.compare_versions(version1.id, version2.id)
            print(f"   ✓ Comparison completed")
            print(f"     - Documents changed: {comparison['statistics_comparison']['documents']['difference']}")
            print(f"     - Chunks changed: {comparison['statistics_comparison']['chunks']['difference']}")
            print(f"     - Tokens changed: {comparison['statistics_comparison']['tokens']['difference']}")
            
            # Test integrity verification
            print("7. Testing integrity verification...")
            integrity1 = version1.verify_integrity()
            integrity2 = version2.verify_integrity()
            print(f"   ✓ Version 1 integrity: {integrity1}")
            print(f"   ✓ Version 2 integrity: {integrity2}")
            
            # Test version history
            print("8. Testing version history...")
            history = ContextVersionService.get_version_history(context.id)
            print(f"   ✓ Retrieved {len(history)} versions from history")
            
            for i, version in enumerate(history):
                print(f"     {i+1}. v{version.version_number} - {version.description[:50]}...")
            
            # Test current version
            print("9. Testing current version detection...")
            current = ContextVersionService.get_current_version(context.id)
            print(f"   ✓ Current version: {current.version_number}")
            
            # Test to_dict serialization
            print("10. Testing serialization...")
            version_dict = version2.to_dict(include_snapshots=True)
            print(f"   ✓ Serialized version {version2.version_number}")
            print(f"     - Keys: {list(version_dict.keys())}")
            print(f"     - Has snapshots: {'config_snapshot' in version_dict}")
            print(f"     - Has tags: {len(version_dict.get('tags', []))} tags")
            
            print("\n" + "=" * 50)
            print("✅ All versioning tests passed successfully!")
            print(f"Created {len(history)} versions for context '{context.name}'")
            
            # Clean up test data
            print("\n11. Cleaning up test data...")
            Context.query.filter_by(user_id=user.id).delete()
            User.query.filter_by(username='version_test_user').delete()
            db.session.commit()
            print("   ✓ Test data cleaned up")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

def main():
    """Run the versioning tests"""
    print("Context Versioning System Test Suite")
    print("===================================")
    
    # Ensure database is initialized
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database initialized")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return 1
    
    # Run tests
    if test_versioning_system():
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n💥 Tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)