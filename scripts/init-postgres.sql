-- 本地开发库：student_service / student_service
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'student_service') THEN
    CREATE ROLE student_service LOGIN PASSWORD 'student_service';
  ELSE
    ALTER ROLE student_service WITH LOGIN PASSWORD 'student_service';
  END IF;
END
$$;

SELECT 'CREATE DATABASE student_service OWNER student_service'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'student_service')\gexec

GRANT ALL PRIVILEGES ON DATABASE student_service TO student_service;
