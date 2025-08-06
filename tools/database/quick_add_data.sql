-- Quick test data for dashboard
-- Run this SQL to add minimal test data

-- Add test patients
INSERT INTO patients (id, external_id, mrn, created_at, updated_at, data_classification, consent_status) 
VALUES 
  (gen_random_uuid(), 'EXT_001', 'MRN0001', NOW(), NOW(), 'phi', '{"status": "granted", "types": ["treatment"]}'),
  (gen_random_uuid(), 'EXT_002', 'MRN0002', NOW(), NOW(), 'phi', '{"status": "granted", "types": ["treatment"]}'),
  (gen_random_uuid(), 'EXT_003', 'MRN0003', NOW(), NOW(), 'phi', '{"status": "granted", "types": ["treatment"]}'),
  (gen_random_uuid(), 'EXT_004', 'MRN0004', NOW(), NOW(), 'phi', '{"status": "granted", "types": ["treatment"]}'),
  (gen_random_uuid(), 'EXT_005', 'MRN0005', NOW(), NOW(), 'phi', '{"status": "granted", "types": ["treatment"]}')
ON CONFLICT (mrn) DO NOTHING;

-- Add test user first
INSERT INTO users (id, email, username, password_hash, role, created_at, updated_at)
VALUES (
  'c4c4fec4-c63a-49d1-a5c7-07495c4740b0'::uuid, 
  'admin@example.com', 
  'admin', 
  'hashed_password', 
  'admin', 
  NOW(), 
  NOW()
) ON CONFLICT (email) DO NOTHING;

-- Add test audit logs with proper enum values
INSERT INTO audit_logs (
  id, timestamp, event_type, user_id, action, result, 
  ip_address, request_method, request_path, response_status_code,
  data_classification, log_hash, created_at, updated_at
) VALUES 
  (gen_random_uuid(), NOW() - INTERVAL '1 hour', 'user_login', 'c4c4fec4-c63a-49d1-a5c7-07495c4740b0'::uuid, 'User login', 'success', '127.0.0.1', 'POST', '/api/v1/auth/login', 200, 'internal', encode(digest('log1', 'sha256'), 'hex'), NOW(), NOW()),
  (gen_random_uuid(), NOW() - INTERVAL '2 hours', 'user_login_failed', 'c4c4fec4-c63a-49d1-a5c7-07495c4740b0'::uuid, 'Failed login', 'failure', '127.0.0.1', 'POST', '/api/v1/auth/login', 401, 'internal', encode(digest('log2', 'sha256'), 'hex'), NOW(), NOW()),
  (gen_random_uuid(), NOW() - INTERVAL '3 hours', 'phi_accessed', 'c4c4fec4-c63a-49d1-a5c7-07495c4740b0'::uuid, 'Patient record accessed', 'success', '127.0.0.1', 'GET', '/api/v1/patients/123', 200, 'phi', encode(digest('log3', 'sha256'), 'hex'), NOW(), NOW()),
  (gen_random_uuid(), NOW() - INTERVAL '4 hours', 'security_violation', 'c4c4fec4-c63a-49d1-a5c7-07495c4740b0'::uuid, 'Suspicious activity', 'error', '192.168.1.100', 'GET', '/api/v1/admin', 403, 'internal', encode(digest('log4', 'sha256'), 'hex'), NOW(), NOW()),
  (gen_random_uuid(), NOW() - INTERVAL '5 hours', 'user_created', 'c4c4fec4-c63a-49d1-a5c7-07495c4740b0'::uuid, 'New user created', 'success', '127.0.0.1', 'POST', '/api/v1/users', 201, 'internal', encode(digest('log5', 'sha256'), 'hex'), NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Check the data
SELECT 'Patients' as table_name, COUNT(*) as count FROM patients
UNION ALL
SELECT 'Audit Logs' as table_name, COUNT(*) as count FROM audit_logs
UNION ALL
SELECT 'Users' as table_name, COUNT(*) as count FROM users;