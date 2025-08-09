-- RAG Chatbot PWA Database Initialization Script
-- Production database setup with optimizations and security

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create additional user for read-only access (for monitoring)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'raguser_readonly') THEN
        CREATE USER raguser_readonly WITH PASSWORD 'readonly123';
        GRANT CONNECT ON DATABASE ragchatbot TO raguser_readonly;
        GRANT USAGE ON SCHEMA public TO raguser_readonly;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO raguser_readonly;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO raguser_readonly;
    END IF;
END
$$;

-- Performance optimizations
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- Memory settings (adjust based on available RAM)
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '8MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Checkpoint settings
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Connection settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 2;
ALTER SYSTEM SET max_parallel_workers = 8;

-- Logging settings
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Reload configuration
SELECT pg_reload_conf();

-- Create indexes for common queries (will be created by SQLAlchemy migrations)
-- These are here as documentation of expected indexes

-- Users table indexes
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Contexts table indexes
-- CREATE INDEX IF NOT EXISTS idx_contexts_user_id ON contexts(user_id);
-- CREATE INDEX IF NOT EXISTS idx_contexts_status ON contexts(status);
-- CREATE INDEX IF NOT EXISTS idx_contexts_source_type ON contexts(source_type);
-- CREATE INDEX IF NOT EXISTS idx_contexts_created_at ON contexts(created_at);

-- Documents table indexes
-- CREATE INDEX IF NOT EXISTS idx_documents_context_id ON documents(context_id);
-- CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
-- CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- Chat sessions table indexes
-- CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
-- CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);

-- Messages table indexes
-- CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
-- CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
-- CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- User preferences table indexes
-- CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
-- CREATE INDEX IF NOT EXISTS idx_user_preferences_category ON user_preferences(category);
-- CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(key);

-- Create a function to generate UUIDs (for future use)
CREATE OR REPLACE FUNCTION generate_uuid() RETURNS TEXT AS $$
BEGIN
    RETURN uuid_generate_v4()::text;
END;
$$ LANGUAGE plpgsql;

-- Create a function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
INSERT INTO pg_stat_statements_reset();
DO $$
BEGIN
    RAISE NOTICE 'RAG Chatbot database initialization completed successfully';
END
$$;