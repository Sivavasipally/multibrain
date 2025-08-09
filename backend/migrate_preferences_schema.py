#!/usr/bin/env python3
"""
Migration script to update user_preferences table schema

This script migrates from the detailed preference schema (category, key, value)
to the simplified JSON schema (preferences column) to match the current model.
"""

import sqlite3
import json
import os
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database before migration"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Read original database
    with open(db_path, 'rb') as original:
        with open(backup_path, 'wb') as backup:
            backup.write(original.read())
    
    print(f"[SUCCESS] Database backed up to: {backup_path}")
    return backup_path

def migrate_preferences_schema(db_path):
    """Migrate user_preferences table from old schema to new schema"""
    print(f"[INFO] Starting preferences schema migration for {db_path}")
    
    # Create backup first
    backup_path = backup_database(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if the old schema exists
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'preferences' in columns:
            print("[SUCCESS] Database already has new schema, no migration needed")
            return
        
        if 'category' not in columns:
            print("[ERROR] Unexpected schema, cannot migrate")
            return
        
        print("[INFO] Found old schema, proceeding with migration...")
        
        # Step 1: Extract existing preference data
        cursor.execute("""
            SELECT user_id, category, key, value, value_type, created_at, updated_at
            FROM user_preferences
        """)
        
        old_preferences = cursor.fetchall()
        print(f"[INFO] Found {len(old_preferences)} individual preferences to migrate")
        
        # Step 2: Group preferences by user_id
        user_preferences = {}
        user_timestamps = {}
        
        for pref in old_preferences:
            user_id = pref['user_id']
            category = pref['category']
            key = pref['key']
            value = pref['value']
            
            if user_id not in user_preferences:
                user_preferences[user_id] = {}
                user_timestamps[user_id] = {
                    'created_at': pref['created_at'],
                    'updated_at': pref['updated_at']
                }
            
            if category not in user_preferences[user_id]:
                user_preferences[user_id][category] = {}
            
            user_preferences[user_id][category][key] = value
        
        print(f"[INFO] Grouped preferences for {len(user_preferences)} users")
        
        # Step 3: Drop old table and create new table
        cursor.execute("DROP TABLE user_preferences")
        
        cursor.execute("""
            CREATE TABLE user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                preferences JSON DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE (user_id)
            )
        """)
        
        print("[SUCCESS] Created new preferences table schema")
        
        # Step 4: Insert migrated data
        for user_id, preferences in user_preferences.items():
            preferences_json = json.dumps(preferences, sort_keys=True)
            timestamps = user_timestamps[user_id]
            
            cursor.execute("""
                INSERT INTO user_preferences (user_id, preferences, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, preferences_json, timestamps['created_at'], timestamps['updated_at']))
        
        conn.commit()
        print(f"[SUCCESS] Successfully migrated {len(user_preferences)} user preference sets")
        
        # Step 5: Verify migration
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        count = cursor.fetchone()[0]
        print(f"[INFO] Verification: {count} user preference records in new schema")
        
        # Display sample
        cursor.execute("SELECT user_id, preferences FROM user_preferences LIMIT 3")
        samples = cursor.fetchall()
        
        for sample in samples:
            user_id = sample[0]
            prefs = json.loads(sample[1]) if sample[1] else {}
            categories = list(prefs.keys())
            print(f"   User {user_id}: {len(categories)} categories ({', '.join(categories[:3])})")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        
        # Restore from backup
        conn.close()
        os.replace(backup_path, db_path)
        print(f"[INFO] Database restored from backup")
        raise
        
    finally:
        conn.close()
    
    print("[SUCCESS] Migration completed successfully!")

if __name__ == '__main__':
    db_path = 'instance/ragchatbot.db'
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        exit(1)
    
    try:
        migrate_preferences_schema(db_path)
        print("\n[SUCCESS] Preferences schema migration completed!")
        print("You can now restart the application.")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print("The database has been restored from backup.")
        exit(1)