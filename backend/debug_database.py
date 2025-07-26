#!/usr/bin/env python3
"""
Debug database issues
"""

import os
import sqlite3
from app_local import app, db

def debug_database():
    """Debug database configuration and schema"""
    print("🔍 Debugging database configuration...")
    
    with app.app_context():
        # Check database configuration
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Database URI: {db_uri}")
        
        # Check if database file exists
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            print(f"Database file path: {db_path}")
            print(f"Database file exists: {os.path.exists(db_path)}")
            
            if os.path.exists(db_path):
                print(f"Database file size: {os.path.getsize(db_path)} bytes")
        
        # Check SQLAlchemy metadata
        print(f"\nSQLAlchemy engine: {db.engine}")
        print(f"SQLAlchemy metadata tables: {list(db.metadata.tables.keys())}")
        
        # Try to inspect the Context model
        from models import Context
        print(f"\nContext model table name: {Context.__tablename__}")
        print(f"Context model columns:")
        for column in Context.__table__.columns:
            print(f"  {column.name}: {column.type} (default: {column.default})")
        
        # Try to create tables
        print(f"\nCreating tables...")
        try:
            db.create_all()
            print("✅ Tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
        
        # Check if tables exist in database
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"\nTables in database: {[table[0] for table in tables]}")
                
                # Check contexts table specifically
                if ('contexts',) in tables:
                    cursor.execute("PRAGMA table_info(contexts)")
                    columns = cursor.fetchall()
                    print(f"\nContexts table columns:")
                    for col in columns:
                        print(f"  {col[1]}: {col[2]} (default: {col[4]})")
                else:
                    print("❌ Contexts table not found in database")
                
                conn.close()

if __name__ == "__main__":
    debug_database()
