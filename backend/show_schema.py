"""
Display current database schema information
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app_local import app, db

def show_database_info():
    """Display comprehensive database information"""
    print("📊 RAG Chatbot Database Schema Information")
    print("=" * 60)
    
    with app.app_context():
        from sqlalchemy import inspect, text
        
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"🗃️  Database Engine: {db.engine.dialect.name}")
            print(f"📋 Total Tables: {len(tables)}")
            print()
            
            for table_name in sorted(tables):
                print(f"📋 Table: {table_name.upper()}")
                print("-" * 40)
                
                columns = inspector.get_columns(table_name)
                
                # Table header
                print(f"{'Column':<20} {'Type':<15} {'Nullable':<8} {'Default':<15} {'Key'}")
                print("-" * 75)
                
                # Get primary keys
                pk_constraint = inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint['constrained_columns'] if pk_constraint else []
                
                # Get foreign keys
                fk_constraints = inspector.get_foreign_keys(table_name)
                foreign_keys = []
                for fk in fk_constraints:
                    foreign_keys.extend(fk['constrained_columns'])
                
                for col in columns:
                    name = col['name']
                    dtype = str(col['type'])
                    nullable = "Yes" if col['nullable'] else "No"
                    default = str(col['default']) if col['default'] is not None else "-"
                    
                    # Determine key type
                    key_type = ""
                    if name in primary_keys:
                        key_type = "PK"
                    elif name in foreign_keys:
                        key_type = "FK"
                    
                    print(f"{name:<20} {dtype:<15} {nullable:<8} {default:<15} {key_type}")
                
                # Show row count
                try:
                    with db.engine.connect() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.fetchone()[0]
                        print(f"\n📊 Row count: {count:,}")
                except Exception as e:
                    print(f"\n⚠️  Could not get row count: {e}")
                
                # Show foreign key relationships
                if fk_constraints:
                    print(f"\n🔗 Foreign Key Relationships:")
                    for fk in fk_constraints:
                        local_cols = ', '.join(fk['constrained_columns'])
                        remote_table = fk['referred_table']
                        remote_cols = ', '.join(fk['referred_columns'])
                        print(f"   {local_cols} → {remote_table}.{remote_cols}")
                
                print("\n" + "=" * 60 + "\n")
            
            # Show database file info
            db_paths = [
                Path(__file__).parent / "ragchatbot.db",
                Path(__file__).parent / "instance" / "ragchatbot.db",
                Path(__file__).parent.parent / "ragchatbot.db"
            ]
            
            for path in db_paths:
                if path.exists():
                    size = path.stat().st_size
                    print(f"💾 Database File: {path}")
                    print(f"📏 File Size: {size:,} bytes ({size/1024:.1f} KB)")
                    break
            
            # Test some sample queries
            print(f"\n🔍 Sample Data:")
            try:
                with db.engine.connect() as conn:
                    # Show users
                    result = conn.execute(text("SELECT username, email, is_admin, created_at FROM users LIMIT 5"))
                    users = result.fetchall()
                    if users:
                        print(f"👥 Recent Users:")
                        for user in users:
                            admin_badge = " (Admin)" if user[2] else ""
                            print(f"   - {user[0]} ({user[1]}){admin_badge}")
                    
                    # Show contexts
                    result = conn.execute(text("SELECT name, source_type, status, total_chunks FROM contexts LIMIT 5"))
                    contexts = result.fetchall()
                    if contexts:
                        print(f"\n📁 Recent Contexts:")
                        for ctx in contexts:
                            print(f"   - {ctx[0]} ({ctx[1]}) - {ctx[2]} - {ctx[3]} chunks")
                    
                    # Show chat sessions
                    result = conn.execute(text("SELECT title, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT 3"))
                    sessions = result.fetchall()
                    if sessions:
                        print(f"\n💬 Recent Chat Sessions:")
                        for session in sessions:
                            print(f"   - {session[0]} ({session[1]})")
                            
            except Exception as e:
                print(f"⚠️  Could not fetch sample data: {e}")
                
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
            return False
        
        return True

def check_schema_health():
    """Check for potential schema issues"""
    print("\n🩺 Schema Health Check")
    print("-" * 30)
    
    issues = []
    warnings = []
    
    with app.app_context():
        from sqlalchemy import inspect
        
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Check for expected tables
            expected_tables = ['users', 'contexts', 'documents', 'text_chunks', 'chat_sessions', 'messages']
            missing_tables = set(expected_tables) - set(tables)
            
            if missing_tables:
                issues.append(f"Missing tables: {', '.join(missing_tables)}")
            
            # Check users table for is_admin column
            if 'users' in tables:
                user_columns = [col['name'] for col in inspector.get_columns('users')]
                if 'is_admin' not in user_columns:
                    issues.append("Missing 'is_admin' column in users table")
                
                # Check if there are any admin users
                try:
                    from sqlalchemy import text
                    with db.engine.connect() as conn:
                        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = 1"))
                        admin_count = result.fetchone()[0]
                        if admin_count == 0:
                            warnings.append("No admin users found")
                except:
                    pass
            
            # Check for orphaned data
            if all(t in tables for t in ['contexts', 'documents']):
                try:
                    from sqlalchemy import text
                    with db.engine.connect() as conn:
                        # Check for documents without contexts
                        result = conn.execute(text("""
                            SELECT COUNT(*) FROM documents d 
                            LEFT JOIN contexts c ON d.context_id = c.id 
                            WHERE c.id IS NULL
                        """))
                        orphaned_docs = result.fetchone()[0]
                        if orphaned_docs > 0:
                            warnings.append(f"{orphaned_docs} orphaned documents found")
                except:
                    pass
            
        except Exception as e:
            issues.append(f"Could not perform health check: {e}")
    
    # Report results
    if not issues and not warnings:
        print("✅ Schema appears healthy!")
    else:
        if issues:
            print("❌ Issues found:")
            for issue in issues:
                print(f"   - {issue}")
        
        if warnings:
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   - {warning}")
    
    return len(issues) == 0

def main():
    """Main function"""
    try:
        success = show_database_info()
        if success:
            check_schema_health()
            print("\n✅ Schema information displayed successfully")
        else:
            print("\n❌ Could not display schema information")
            return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)