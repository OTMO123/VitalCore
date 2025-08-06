-- Test database initialization script
-- This script sets up the test database with necessary extensions and initial data

-- Enable necessary PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS test_audit;
CREATE SCHEMA IF NOT EXISTS test_temp;

-- Set up permissions for test user
GRANT ALL PRIVILEGES ON SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON SCHEMA test_audit TO test_user;
GRANT ALL PRIVILEGES ON SCHEMA test_temp TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;

-- Create test-specific functions
CREATE OR REPLACE FUNCTION test_cleanup()
RETURNS void AS $$
BEGIN
    -- Truncate all tables in the correct order (respecting foreign keys)
    TRUNCATE TABLE audit_logs CASCADE;
    TRUNCATE TABLE iris_api_logs CASCADE;
    TRUNCATE TABLE purge_policies CASCADE;
    TRUNCATE TABLE users CASCADE;
    
    -- Reset sequences
    ALTER SEQUENCE IF EXISTS audit_logs_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS iris_api_logs_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS purge_policies_id_seq RESTART WITH 1;
    ALTER SEQUENCE IF EXISTS users_id_seq RESTART WITH 1;
END;
$$ LANGUAGE plpgsql;

-- Create test data generation function
CREATE OR REPLACE FUNCTION generate_test_users(count integer DEFAULT 10)
RETURNS void AS $$
DECLARE
    i integer;
BEGIN
    FOR i IN 1..count LOOP
        INSERT INTO users (
            username, 
            email, 
            hashed_password, 
            role, 
            is_active, 
            is_verified,
            created_at,
            updated_at
        ) VALUES (
            'testuser' || i,
            'testuser' || i || '@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LbPp6FBmT8oS.UOA2', -- password: testpass
            CASE WHEN i % 5 = 0 THEN 'admin' ELSE 'user' END,
            true,
            true,
            NOW() - INTERVAL '1 day' * (i % 30),
            NOW() - INTERVAL '1 hour' * (i % 24)
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create test audit log generation function
CREATE OR REPLACE FUNCTION generate_test_audit_logs(count integer DEFAULT 100)
RETURNS void AS $$
DECLARE
    i integer;
    user_ids integer[];
    event_types text[] := ARRAY[
        'user.login.success', 'user.login.failure', 'user.logout',
        'data.created', 'data.updated', 'data.deleted',
        'iris.api.request', 'iris.api.response', 'iris.api.error'
    ];
BEGIN
    -- Get available user IDs
    SELECT ARRAY(SELECT id::text FROM users LIMIT 20) INTO user_ids;
    
    FOR i IN 1..count LOOP
        INSERT INTO audit_logs (
            event_type,
            user_id,
            session_id,
            resource_type,
            resource_id,
            action,
            outcome,
            ip_address,
            event_data,
            created_at
        ) VALUES (
            event_types[1 + (i % array_length(event_types, 1))],
            user_ids[1 + (i % array_length(user_ids, 1))],
            'session_' || (i % 50),
            CASE WHEN i % 3 = 0 THEN 'user' WHEN i % 3 = 1 THEN 'record' ELSE 'system' END,
            'resource_' || i,
            'test_action_' || (i % 10),
            CASE WHEN i % 10 = 0 THEN 'failure' ELSE 'success' END,
            '192.168.1.' || (1 + (i % 254)),
            jsonb_build_object(
                'test_id', i,
                'random_value', random(),
                'timestamp', NOW()
            ),
            NOW() - INTERVAL '1 minute' * i
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create test performance data
CREATE OR REPLACE FUNCTION create_test_performance_data()
RETURNS void AS $$
BEGIN
    -- Create a large table for performance testing
    DROP TABLE IF EXISTS test_performance;
    CREATE TABLE test_performance (
        id SERIAL PRIMARY KEY,
        data jsonb,
        indexed_field text,
        created_at timestamp DEFAULT NOW()
    );
    
    -- Insert test data
    INSERT INTO test_performance (data, indexed_field)
    SELECT 
        jsonb_build_object(
            'id', generate_series,
            'name', 'test_record_' || generate_series,
            'value', random() * 1000,
            'nested', jsonb_build_object('key', 'value_' || generate_series)
        ),
        'indexed_' || (generate_series % 100)
    FROM generate_series(1, 10000);
    
    -- Create indexes for performance testing
    CREATE INDEX IF NOT EXISTS idx_test_performance_indexed_field ON test_performance(indexed_field);
    CREATE INDEX IF NOT EXISTS idx_test_performance_data_gin ON test_performance USING GIN(data);
END;
$$ LANGUAGE plpgsql;

-- Create test data cleanup function
CREATE OR REPLACE FUNCTION cleanup_test_data()
RETURNS void AS $$
BEGIN
    -- Clean up test-specific data
    DELETE FROM audit_logs WHERE event_type LIKE 'test.%';
    DELETE FROM users WHERE username LIKE 'testuser%';
    DROP TABLE IF EXISTS test_performance;
    
    -- Reset sequences to start values
    PERFORM setval('audit_logs_id_seq', COALESCE(MAX(id), 1)) FROM audit_logs;
    PERFORM setval('users_id_seq', COALESCE(MAX(id), 1)) FROM users;
END;
$$ LANGUAGE plpgsql;

-- Set up test database configuration
ALTER DATABASE test_iris_db SET timezone TO 'UTC';
ALTER DATABASE test_iris_db SET log_statement TO 'all';
ALTER DATABASE test_iris_db SET log_min_duration_statement TO 0;

-- Grant execute permissions on test functions
GRANT EXECUTE ON FUNCTION test_cleanup() TO test_user;
GRANT EXECUTE ON FUNCTION generate_test_users(integer) TO test_user;
GRANT EXECUTE ON FUNCTION generate_test_audit_logs(integer) TO test_user;
GRANT EXECUTE ON FUNCTION create_test_performance_data() TO test_user;
GRANT EXECUTE ON FUNCTION cleanup_test_data() TO test_user;

-- Create test monitoring views
CREATE OR REPLACE VIEW test_database_stats AS
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

GRANT SELECT ON test_database_stats TO test_user;