-- Add test patients to fix dashboard patient count
-- Run this with: psql -h localhost -p 5433 -U test_user -d test_iris_db -f add_patients.sql

-- First, check current patient count
SELECT 'Current patient count:' as info, COUNT(*) as count FROM patients WHERE soft_deleted_at IS NULL;

-- Add test patients
INSERT INTO patients (
    id, external_id, mrn, first_name_encrypted, last_name_encrypted, 
    date_of_birth_encrypted, data_classification, consent_status,
    created_at, updated_at
) VALUES 
    (gen_random_uuid(), 'EXT_MRN001', 'MRN001', 'encrypted_John_001', 'encrypted_Doe_001', 'encrypted_1985-03-15_001', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '1 day', NOW()),
    (gen_random_uuid(), 'EXT_MRN002', 'MRN002', 'encrypted_Jane_002', 'encrypted_Smith_002', 'encrypted_1990-07-22_002', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '2 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN003', 'MRN003', 'encrypted_Michael_003', 'encrypted_Johnson_003', 'encrypted_1978-11-30_003', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '3 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN004', 'MRN004', 'encrypted_Sarah_004', 'encrypted_Williams_004', 'encrypted_1982-04-18_004', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '4 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN005', 'MRN005', 'encrypted_David_005', 'encrypted_Brown_005', 'encrypted_1975-09-12_005', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '5 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN006', 'MRN006', 'encrypted_Emily_006', 'encrypted_Davis_006', 'encrypted_1988-01-25_006', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '6 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN007', 'MRN007', 'encrypted_Chris_007', 'encrypted_Miller_007', 'encrypted_1992-06-08_007', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '7 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN008', 'MRN008', 'encrypted_Ashley_008', 'encrypted_Wilson_008', 'encrypted_1986-12-03_008', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '8 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN009', 'MRN009', 'encrypted_Matthew_009', 'encrypted_Moore_009', 'encrypted_1980-08-14_009', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '9 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN010', 'MRN010', 'encrypted_Jessica_010', 'encrypted_Taylor_010', 'encrypted_1994-02-28_010', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '10 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN011', 'MRN011', 'encrypted_James_011', 'encrypted_Anderson_011', 'encrypted_1983-05-19_011', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '11 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN012', 'MRN012', 'encrypted_Amanda_012', 'encrypted_Thomas_012', 'encrypted_1987-10-07_012', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '12 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN013', 'MRN013', 'encrypted_Daniel_013', 'encrypted_Jackson_013', 'encrypted_1979-03-26_013', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '13 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN014', 'MRN014', 'encrypted_Melissa_014', 'encrypted_White_014', 'encrypted_1991-11-15_014', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '14 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN015', 'MRN015', 'encrypted_Robert_015', 'encrypted_Harris_015', 'encrypted_1984-07-09_015', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '15 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN016', 'MRN016', 'encrypted_Jennifer_016', 'encrypted_Martin_016', 'encrypted_1989-04-02_016', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '16 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN017', 'MRN017', 'encrypted_William_017', 'encrypted_Thompson_017', 'encrypted_1976-12-20_017', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '17 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN018', 'MRN018', 'encrypted_Lisa_018', 'encrypted_Garcia_018', 'encrypted_1993-08-11_018', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '18 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN019', 'MRN019', 'encrypted_Joseph_019', 'encrypted_Martinez_019', 'encrypted_1981-01-17_019', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '19 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN020', 'MRN020', 'encrypted_Karen_020', 'encrypted_Rodriguez_020', 'encrypted_1985-06-24_020', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '20 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN021', 'MRN021', 'encrypted_Charles_021', 'encrypted_Clark_021', 'encrypted_1977-09-05_021', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '21 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN022', 'MRN022', 'encrypted_Nancy_022', 'encrypted_Lee_022', 'encrypted_1990-03-13_022', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '22 days', NOW()),
    (gen_random_uuid(), 'EXT_MRN023', 'MRN023', 'encrypted_Thomas_023', 'encrypted_Walker_023', 'encrypted_1986-11-28_023', 'PHI', '{"status": "granted", "types": ["treatment"]}', NOW() - INTERVAL '23 days', NOW())
ON CONFLICT (mrn) DO NOTHING;

-- Check final patient count
SELECT 'Final patient count:' as info, COUNT(*) as count FROM patients WHERE soft_deleted_at IS NULL;

-- Show patients by creation date
SELECT 'Patients by week:' as info, 
       CASE 
           WHEN created_at >= NOW() - INTERVAL '7 days' THEN 'This week'
           WHEN created_at >= NOW() - INTERVAL '14 days' THEN 'Last week'
           ELSE 'Older'
       END as time_period,
       COUNT(*) as count
FROM patients 
WHERE soft_deleted_at IS NULL 
GROUP BY time_period
ORDER BY time_period;