-- =============================================================================
-- ProveIT 2026 Demo Stack - PostgreSQL Database Initialization Script
-- =============================================================================
-- Description: This script creates the databases and users for all Ignition
-- gateways in the ProveIT stack. Each gateway gets its own database and user
-- with appropriate permissions.
--
-- Security Note: Passwords are set using environment variables in docker-compose
-- =============================================================================

-- Set default connection parameters
\set ON_ERROR_STOP on
SET client_encoding = 'UTF8';

-- =============================================================================
-- CREATE DATABASES
-- =============================================================================

-- Core Gateway Database
CREATE DATABASE ignition_core
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100;

-- SCADA Gateway Database
CREATE DATABASE ignition_scada
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100;

-- MES Frontend Gateway Database
CREATE DATABASE ignition_mes_frontend
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100;

-- MES Backend Gateway Database
CREATE DATABASE ignition_mes_backend
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100;

-- =============================================================================
-- CREATE USERS/ROLES
-- =============================================================================
-- Note: Passwords are injected via environment variables for security

-- Core Gateway User
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ignition_core') THEN
        EXECUTE format('CREATE USER ignition_core WITH PASSWORD %L',
            COALESCE(current_setting('app.core_password', true), 'password'));
    END IF;
END $$;

-- SCADA Gateway User
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ignition_scada') THEN
        EXECUTE format('CREATE USER ignition_scada WITH PASSWORD %L',
            COALESCE(current_setting('app.scada_password', true), 'password'));
    END IF;
END $$;

-- MES Frontend Gateway User
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ignition_mes_frontend') THEN
        EXECUTE format('CREATE USER ignition_mes_frontend WITH PASSWORD %L',
            COALESCE(current_setting('app.mes_frontend_password', true), 'password'));
    END IF;
END $$;

-- MES Backend Gateway User
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ignition_mes_backend') THEN
        EXECUTE format('CREATE USER ignition_mes_backend WITH PASSWORD %L',
            COALESCE(current_setting('app.mes_backend_password', true), 'password'));
    END IF;
END $$;

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

-- Core Gateway Permissions
GRANT CONNECT ON DATABASE ignition_core TO ignition_core;
\connect ignition_core
GRANT ALL PRIVILEGES ON DATABASE ignition_core TO ignition_core;
GRANT CREATE ON SCHEMA public TO ignition_core;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ignition_core;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ignition_core;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ignition_core;

-- SCADA Gateway Permissions
\connect postgres
GRANT CONNECT ON DATABASE ignition_scada TO ignition_scada;
\connect ignition_scada
GRANT ALL PRIVILEGES ON DATABASE ignition_scada TO ignition_scada;
GRANT CREATE ON SCHEMA public TO ignition_scada;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ignition_scada;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ignition_scada;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ignition_scada;

-- MES Frontend Gateway Permissions
\connect postgres
GRANT CONNECT ON DATABASE ignition_mes_frontend TO ignition_mes_frontend;
\connect ignition_mes_frontend
GRANT ALL PRIVILEGES ON DATABASE ignition_mes_frontend TO ignition_mes_frontend;
GRANT CREATE ON SCHEMA public TO ignition_mes_frontend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ignition_mes_frontend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ignition_mes_frontend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ignition_mes_frontend;

-- MES Backend Gateway Permissions
\connect postgres
GRANT CONNECT ON DATABASE ignition_mes_backend TO ignition_mes_backend;
\connect ignition_mes_backend
GRANT ALL PRIVILEGES ON DATABASE ignition_mes_backend TO ignition_mes_backend;
GRANT CREATE ON SCHEMA public TO ignition_mes_backend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ignition_mes_backend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ignition_mes_backend;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ignition_mes_backend;

-- =============================================================================
-- PERFORMANCE & MONITORING CONFIGURATIONS
-- =============================================================================

\connect postgres

-- Create a monitoring user with read-only access to all databases
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'monitoring_readonly') THEN
        EXECUTE format('CREATE USER monitoring_readonly WITH PASSWORD %L',
            COALESCE(current_setting('app.monitoring_password', true), 'password'));
    END IF;
END $$;

-- Grant connect privileges to monitoring user
GRANT CONNECT ON DATABASE ignition_core TO monitoring_readonly;
GRANT CONNECT ON DATABASE ignition_scada TO monitoring_readonly;
GRANT CONNECT ON DATABASE ignition_mes_frontend TO monitoring_readonly;
GRANT CONNECT ON DATABASE ignition_mes_backend TO monitoring_readonly;

-- Grant usage on schemas (will be applied when schemas are created)
\connect ignition_core
GRANT USAGE ON SCHEMA public TO monitoring_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;

\connect ignition_scada
GRANT USAGE ON SCHEMA public TO monitoring_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;

\connect ignition_mes_frontend
GRANT USAGE ON SCHEMA public TO monitoring_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;

\connect ignition_mes_backend
GRANT USAGE ON SCHEMA public TO monitoring_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;

-- =============================================================================
-- IGNITION-SPECIFIC OPTIMIZATIONS
-- =============================================================================

-- These settings optimize PostgreSQL for Ignition's typical workload patterns
\connect postgres

-- Create extension for UUID generation (used by Ignition)
\connect ignition_core
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\connect ignition_scada
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\connect ignition_mes_frontend
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\connect ignition_mes_backend
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- VERIFICATION
-- =============================================================================

\connect postgres

-- List all databases
SELECT datname AS "Database",
       pg_catalog.pg_get_userbyid(datdba) AS "Owner",
       pg_catalog.pg_encoding_to_char(encoding) AS "Encoding"
FROM pg_catalog.pg_database
WHERE datname LIKE 'ignition%'
ORDER BY datname;

-- List all users
SELECT usename AS "User",
       CASE
         WHEN usesuper THEN 'SUPERUSER'
         WHEN usecreatedb THEN 'CREATEDB'
         ELSE 'REGULAR'
       END AS "Type"
FROM pg_catalog.pg_user
WHERE usename LIKE 'ignition%' OR usename = 'monitoring_readonly'
ORDER BY usename;

-- Display success message
\echo 'Database initialization completed successfully!'
\echo 'Created databases: ignition_core, ignition_scada, ignition_mes_frontend, ignition_mes_backend'
\echo 'Created users: ignition_core, ignition_scada, ignition_mes_frontend, ignition_mes_backend, monitoring_readonly'
\echo 'Remember to update passwords in the .env file for production use!'