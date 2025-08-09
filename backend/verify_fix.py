"""
Verify that the database fix was successful
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "instance" / "ragchatbot.db"

if db_path.exists():
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("✅ Users table structure:")
        print("ID | Name         | Type    | NotNull | Default | PrimaryKey")
        print("-" * 60)
        for column in columns:
            cid, name, dtype, notnull, default, pk = column
            default_str = str(default) if default is not None else "None"
            print(f"{cid:2} | {name:12} | {dtype:7} | {notnull:7} | {default_str:7} | {pk}")
        
        # Check if is_admin column exists
        column_names = [col[1] for col in columns]
        if 'is_admin' in column_names:
            print("\n🎉 SUCCESS: is_admin column found in users table!")
            
            # Check if any users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"👥 Current user count: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT username, is_admin FROM users")
                users = cursor.fetchall()
                print("\n👤 Current users:")
                for username, is_admin in users:
                    admin_status = "Admin" if is_admin else "Regular User"
                    print(f"  - {username}: {admin_status}")
        else:
            print("\n❌ ERROR: is_admin column NOT found!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"❌ Database file not found at {db_path}")