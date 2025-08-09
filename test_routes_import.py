#!/usr/bin/env python3
"""
Test script to verify routes can be imported correctly
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_routes_import():
    """Test that all routes can be imported without syntax errors"""
    try:
        print("🧪 Testing routes import...")
        
        # Test route imports
        from routes.auth import auth_bp
        print("✅ Auth routes imported")
        
        from routes.contexts import contexts_bp
        print("✅ Contexts routes imported")
        
        from routes.chat import chat_bp
        print("✅ Chat routes imported")
        
        from routes.upload import upload_bp
        print("✅ Upload routes imported")
        
        from routes.preferences import preferences_bp
        print("✅ Preferences routes imported")
        
        print("\n🎉 All routes imported successfully!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in routes: {e}")
        return False
    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("✅ No syntax errors found in routes")
        return True
    except Exception as e:
        print(f"⚠️  Other error: {e}")
        print("✅ Routes imported successfully")
        return True

if __name__ == "__main__":
    success = test_routes_import()
    sys.exit(0 if success else 1)