#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly after fixing circular imports
"""

try:
    print("Testing database import...")
    from database import db
    print("✓ Database import successful")
    
    print("Testing models import...")
    from models import User, Context, Document, ChatSession, Message, TextChunk, TimestampMixin
    print("✓ Base models import successful")
    
    print("Testing extended models import...")
    from context_versioning import ContextVersion, ContextVersionDiff, VersionTag, ContextVersionService
    print("✓ Context versioning models import successful")
    
    print("Testing preferences models import...")
    from user_preferences import UserPreferences, PreferenceTemplate  
    print("✓ User preferences models import successful")
    
    print("Testing extended models through models.py...")
    from models import ContextVersion, ContextVersionDiff, VersionTag, ContextVersionService
    from models import UserPreferences, PreferenceTemplate
    print("✓ Extended models available through models.py")
    
    print("\n🎉 All imports successful! The circular import issue has been resolved.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("There may still be circular import issues to resolve.")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("There may be other issues with the code structure.")