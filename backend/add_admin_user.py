#!/usr/bin/env python3
"""
Simple script to add admin user to existing RAG Chatbot database
Does not require Flask dependencies - uses direct SQLite connection
"""

import sqlite3
import hashlib
import os
import secrets
import base64
from pathlib import Path
from datetime import datetime

def find_database():
    """Find the database file"""
    possible_paths = [
        Path(__file__).parent / "ragchatbot.db",
        Path(__file__).parent / "instance" / "ragchatbot.db",
        Path(__file__).parent.parent / "ragchatbot.db"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def hash_password(password):
    """Simple password hashing compatible with Werkzeug"""
    # Using pbkdf2:sha256 method similar to Werkzeug
    import hashlib
    import secrets
    import base64
    
    # Generate salt
    salt = secrets.token_bytes(16)
    
    # Hash password with salt
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
    
    # Format like Werkzeug
    b64_salt = base64.b64encode(salt).decode('ascii')
    b64_key = base64.b64encode(key).decode('ascii')
    
    return f"pbkdf2:sha256:260000${b64_salt}${b64_key}"

def add_admin_user():
    """Add admin user to the database"""
    db_path = find_database()
    
    if not db_path:
        print("❌ Database file not found!")
        return False
    
    print(f"📁 Found database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id, username, is_admin FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            user_id, username, is_admin = existing_admin
            if is_admin:
                print(f"✅ Admin user '{username}' already exists and has admin privileges")
                return True
            else:
                # Update existing user to be admin
                cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
                print(f"✅ Updated existing user '{username}' to admin")
                conn.commit()
                return True
        
        # Check if users table has is_admin column
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            print("⚠️  Adding missing is_admin column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ Added is_admin column")
        
        # Hash the password
        password_hash = hash_password('admin123')
        current_time = datetime.now().isoformat()
        
        # Insert admin user
        insert_query = """
        INSERT INTO users (username, email, password_hash, created_at, is_active, is_admin)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            'admin',
            'admin@ragchatbot.local',
            password_hash,
            current_time,
            1,  # is_active = True
            1   # is_admin = True
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        print("✅ Successfully created admin user:")
        print(f"   👤 Username: admin")
        print(f"   📧 Email: admin@ragchatbot.local")
        print(f"   🔑 Password: admin123")
        print(f"   🆔 User ID: {user_id}")
        print(f"   👑 Admin: Yes")
        
        # Verify the user was created
        cursor.execute("SELECT id, username, email, is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"✅ Verification: User created successfully")
            print(f"   ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Admin: {'Yes' if user[3] else 'No'}")
        else:
            print("❌ Verification failed - user not found")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding admin user: {e}")
        return False

def show_current_users():
    """Show all current users"""
    db_path = find_database()
    
    if not db_path:
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email, is_admin, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("\n👥 Current Users:")
        print("-" * 60)
        
        if not users:
            print("   No users found")
        else:
            for user in users:
                user_id, username, email, is_admin, created_at = user
                admin_badge = " 👑" if is_admin else ""
                print(f"   {user_id}: {username} ({email}){admin_badge}")
        
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not show users: {e}")

def main():
    """Main function"""
    print("🚀 RAG Chatbot - Add Admin User Tool")
    print("=" * 50)
    
    # Show current users first
    show_current_users()
    
    print("\n🔄 Adding admin user...")
    
    success = add_admin_user()
    
    if success:
        print("\n🎉 Admin user setup completed successfully!")
        print("\n🔐 You can now login with:")
        print("   Username: admin")
        print("   Password: admin123")
        
        # Show updated user list
        show_current_users()
    else:
        print("\n❌ Failed to add admin user")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)