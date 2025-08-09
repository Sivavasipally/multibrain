-- RAG Chatbot PWA Database Initialization Script - Staging Environment
-- Staging database setup with development-friendly configurations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create additional users for testing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'test_user') THEN
        CREATE USER test_user WITH PASSWORD 'test123';
        GRANT CONNECT ON DATABASE ragchatbot_staging TO test_user;
        GRANT USAGE ON SCHEMA public TO test_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO test_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO test_user;
    END IF;
END
$$;

-- Staging-friendly settings (more verbose logging, lower performance requirements)
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
ALTER SYSTEM SET log_statement = 'all';  -- Log all statements in staging
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- Memory settings for staging (smaller requirements)
ALTER SYSTEM SET shared_buffers = '128MB';
ALTER SYSTEM SET effective_cache_size = '512MB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '32MB';

-- Connection settings for staging
ALTER SYSTEM SET max_connections = 100;

-- Reload configuration
SELECT pg_reload_conf();

-- Create some test data (optional)
DO $$
BEGIN
    -- This will be populated by the application initialization
    RAISE NOTICE 'RAG Chatbot staging database initialization completed';
END
$$;