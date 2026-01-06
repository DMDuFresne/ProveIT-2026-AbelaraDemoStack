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

-- Edge Gateway Database
CREATE DATABASE ignition_edge
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100;

-- Shared Database (accessible by all gateways for common lookup tables and master data)
CREATE DATABASE ignition_shared
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

-- Edge Gateway User
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ignition_edge') THEN
        EXECUTE format('CREATE USER ignition_edge WITH PASSWORD %L',
            COALESCE(current_setting('app.edge_password', true), 'password'));
    END IF;
END $$;

-- Shared Database User (OWNER with full write access)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ignition_shared') THEN
        EXECUTE format('CREATE USER ignition_shared WITH PASSWORD %L',
            COALESCE(current_setting('app.shared_password', true), 'password'));
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

-- Edge Gateway Permissions
\connect postgres
GRANT CONNECT ON DATABASE ignition_edge TO ignition_edge;
\connect ignition_edge
GRANT ALL PRIVILEGES ON DATABASE ignition_edge TO ignition_edge;
GRANT CREATE ON SCHEMA public TO ignition_edge;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ignition_edge;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ignition_edge;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ignition_edge;

-- =============================================================================
-- SHARED DATABASE PERMISSIONS
-- =============================================================================
-- The shared database is used for common lookup tables, master data, and
-- cross-gateway reference data. The ignition_shared user is the OWNER with
-- full write access. All gateway users have READ access.

-- Shared Database Owner Permissions (ignition_shared user)
\connect postgres
GRANT CONNECT ON DATABASE ignition_shared TO ignition_shared;
\connect ignition_shared
GRANT ALL PRIVILEGES ON DATABASE ignition_shared TO ignition_shared;
GRANT CREATE ON SCHEMA public TO ignition_shared;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ignition_shared;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ignition_shared;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ignition_shared;

-- Grant CONNECT to all gateway users on the shared database
\connect postgres
GRANT CONNECT ON DATABASE ignition_shared TO ignition_core;
GRANT CONNECT ON DATABASE ignition_shared TO ignition_scada;
GRANT CONNECT ON DATABASE ignition_shared TO ignition_mes_frontend;
GRANT CONNECT ON DATABASE ignition_shared TO ignition_mes_backend;
GRANT CONNECT ON DATABASE ignition_shared TO ignition_edge;

-- Grant READ access (SELECT) to all gateway users on the shared database
\connect ignition_shared
GRANT USAGE ON SCHEMA public TO ignition_core;
GRANT USAGE ON SCHEMA public TO ignition_scada;
GRANT USAGE ON SCHEMA public TO ignition_mes_frontend;
GRANT USAGE ON SCHEMA public TO ignition_mes_backend;
GRANT USAGE ON SCHEMA public TO ignition_edge;

-- Grant SELECT on all existing tables (for any pre-existing tables)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ignition_core;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ignition_scada;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ignition_mes_frontend;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ignition_mes_backend;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ignition_edge;

-- Set default privileges so future tables created by ignition_shared are readable by all gateways
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON TABLES TO ignition_core;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON TABLES TO ignition_scada;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON TABLES TO ignition_mes_frontend;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON TABLES TO ignition_mes_backend;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON TABLES TO ignition_edge;

-- Grant SELECT on sequences for any tables with serial/identity columns
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ignition_core;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ignition_scada;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ignition_mes_frontend;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ignition_mes_backend;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ignition_edge;

-- Set default privileges for sequences
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON SEQUENCES TO ignition_core;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON SEQUENCES TO ignition_scada;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON SEQUENCES TO ignition_mes_frontend;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON SEQUENCES TO ignition_mes_backend;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON SEQUENCES TO ignition_edge;

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
GRANT CONNECT ON DATABASE ignition_edge TO monitoring_readonly;
GRANT CONNECT ON DATABASE ignition_shared TO monitoring_readonly;

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

\connect ignition_edge
GRANT USAGE ON SCHEMA public TO monitoring_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;

\connect ignition_shared
GRANT USAGE ON SCHEMA public TO monitoring_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE ignition_shared IN SCHEMA public GRANT SELECT ON TABLES TO monitoring_readonly;

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

\connect ignition_edge
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\connect ignition_shared
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
\echo 'Created databases: ignition_core, ignition_scada, ignition_mes_frontend, ignition_mes_backend, ignition_edge, ignition_shared'
\echo 'Created users: ignition_core, ignition_scada, ignition_mes_frontend, ignition_mes_backend, ignition_edge, ignition_shared, monitoring_readonly'
\echo 'Shared database (ignition_shared): ignition_shared user has OWNER/write access, all gateway users have READ access'
\echo 'Remember to update passwords in the .env file for production use!'