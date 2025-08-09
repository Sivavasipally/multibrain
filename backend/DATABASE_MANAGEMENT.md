# 🗃️ Database Management Scripts

This directory contains several Python scripts for managing the RAG Chatbot database schema and data.

## 📋 Available Scripts

### 1. `simple_schema_viewer.py` - View Current Schema
**Purpose**: Display current database structure without Flask dependencies

**Usage**:
```bash
python3 simple_schema_viewer.py
```

**What it shows**:
- Database file location and size
- All tables with column definitions
- Row counts for each table  
- Sample data from key tables (users, contexts)
- Primary keys and data types

### 2. `reset_database.py` - Complete Schema Reset
**Purpose**: Drop and recreate the entire database with fresh schema

**Usage**:
```bash
python3 reset_database.py
```

**What it does**:
- 🔄 Creates automatic backup of existing database
- 🗑️ Drops all existing tables and data
- 🔨 Creates fresh schema with latest structure
- 👥 Adds sample users for testing
- ✅ Verifies schema integrity

**Sample users created**:
- `admin` / `admin123` (Admin user)
- `testuser` / `test123` (Regular user)
- `demo` / `demo123` (Demo user with sample context)

### 3. `show_schema.py` - Detailed Schema Analysis
**Purpose**: Comprehensive database analysis with Flask integration

**Usage**:
```bash
python3 show_schema.py
```

**Features**:
- Full table analysis with relationships
- Foreign key mapping
- Schema health check
- Orphaned data detection
- Performance metrics

### 4. `fix_admin_column.py` - Fix Missing Columns
**Purpose**: Add missing `is_admin` column to existing database

**Usage**:
```bash
python3 fix_admin_column.py
```

**What it fixes**:
- Adds `is_admin BOOLEAN DEFAULT 0` to users table
- Preserves all existing data
- Shows before/after table structure

### 5. `verify_fix.py` - Verify Database State
**Purpose**: Quick verification that database is in correct state

**Usage**:
```bash
python3 verify_fix.py
```

**Checks**:
- Confirms `is_admin` column exists
- Shows current users and their admin status
- Displays table structure

## 🚨 Common Issues & Solutions

### Issue: "no such column: users.is_admin"
**Solution**: Run the fix script
```bash
python3 fix_admin_column.py
```

### Issue: Corrupted or inconsistent schema
**Solution**: Reset the entire database
```bash
python3 reset_database.py
```
⚠️ **Warning**: This will delete all existing data!

### Issue: Want to see current database state
**Solution**: Use the schema viewer
```bash
python3 simple_schema_viewer.py
```

## 📊 Current Database Schema

Based on the latest analysis, the database contains these tables:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **users** | User accounts | `id`, `username`, `email`, `is_admin` |
| **contexts** | Knowledge bases | `id`, `name`, `user_id`, `source_type`, `status` |
| **documents** | Uploaded files | `id`, `context_id`, `filename`, `file_path` |
| **text_chunks** | Processed text chunks | `id`, `context_id`, `content`, `chunk_index` |
| **chat_sessions** | Chat conversations | `id`, `user_id`, `title` |
| **messages** | Chat messages | `id`, `session_id`, `role`, `content` |

## 🔄 Migration Workflow

### For Development:
1. Use `simple_schema_viewer.py` to see current state
2. Use `fix_admin_column.py` for small fixes
3. Use `reset_database.py` for major changes

### For Production:
1. **Always backup first**: The scripts create automatic backups
2. Test changes in development environment
3. Use targeted fixes rather than full resets
4. Verify with `verify_fix.py` after changes

## 🛡️ Backup Strategy

All scripts automatically create backups:
- **Location**: Same directory as database
- **Format**: `ragchatbot_backup_YYYYMMDD_HHMMSS.db`
- **When**: Before any destructive operation

### Manual Backup:
```bash
cp instance/ragchatbot.db ragchatbot_backup_$(date +%Y%m%d_%H%M%S).db
```

## 🧪 Testing Database Changes

### 1. Check Current State:
```bash
python3 simple_schema_viewer.py
```

### 2. Make Changes:
```bash
python3 fix_admin_column.py  # or reset_database.py
```

### 3. Verify Changes:
```bash
python3 verify_fix.py
```

### 4. Test Application:
```bash
python3 app_local.py
```

## 📝 Adding New Migrations

To add new database changes:

1. **Update models** in `models.py`
2. **Create migration script** similar to `fix_admin_column.py`
3. **Add to reset script** in `reset_database.py`
4. **Test thoroughly** with sample data

## 🔍 Troubleshooting

### Database Lock Errors:
- Stop the Flask application first
- Close any open database connections
- Try the operation again

### Permission Errors:
- Ensure you have write access to the database directory
- Check file ownership and permissions

### Module Not Found Errors:
- Use `simple_schema_viewer.py` instead of Flask-dependent scripts
- Install required dependencies: `pip install flask sqlalchemy`

---

💡 **Pro Tip**: Always run `simple_schema_viewer.py` first to understand your current database state before making any changes!