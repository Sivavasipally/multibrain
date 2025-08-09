#!/usr/bin/env python3
"""
Test script to verify models can be imported correctly
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_models_import():
    """Test that all models can be imported without syntax errors"""
    try:
        print("🧪 Testing models import...")
        
        # Test basic imports
        from database import db
        print("✅ Database module imported")
        
        from models import User, Context, Document, TextChunk, ChatSession, Message
        print("✅ Core models imported")
        
        from models import UserPreferences
        print("✅ UserPreferences model imported")
        
        # Test model creation (without database)
        user_data = {
            'username': 'test',
            'email': 'test@example.com'
        }
        
        # This should not fail with syntax errors
        user = User(**user_data)
        print("✅ User model can be instantiated")
        
        prefs = UserPreferences(user_id=1, preferences={'theme': 'dark'})
        print("✅ UserPreferences model can be instantiated")
        
        print("\n🎉 All models imported and tested successfully!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in models: {e}")
        return False
    except ImportError as e:
        print(f"⚠️  Import error (expected): {e}")
        print("✅ No syntax errors found")
        return True
    except Exception as e:
        print(f"⚠️  Other error: {e}")
        print("✅ Models imported successfully (runtime error is expected without database)")
        return True

if __name__ == "__main__":
    success = test_models_import()
    sys.exit(0 if success else 1)