#!/bin/bash
# ===============================================================
# Database: mes
# Description: Read-Only User for MCP (Model Context Protocol) Access
#
# This script creates a dedicated read-only database user for AI/LLM
# tools connecting via MCP. This provides defense-in-depth security
# by ensuring that even if the MCP server's read-only transaction
# protection is bypassed, no data modification is possible.
#
# Environment Variables:
#   MCP_READONLY_PASSWORD - Password for the mcp_readonly user
#
# Author(s):
# -- Dylan DuFresne
# ===============================================================

set -e

# Use environment variable or default
MCP_PASSWORD="${MCP_READONLY_PASSWORD:-mcp_readonly_password}"

echo "Creating MCP read-only user..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

    -- ===============================================================
    -- Role: mcp_readonly
    -- Description: Read-only access for MCP/AI integrations
    -- ===============================================================

    DO
    \$\$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'mcp_readonly'
        ) THEN
            CREATE ROLE mcp_readonly LOGIN PASSWORD '${MCP_PASSWORD}';
        ELSE
            -- Update password if role already exists
            ALTER ROLE mcp_readonly WITH PASSWORD '${MCP_PASSWORD}';
        END IF;
    END
    \$\$;

    COMMENT ON ROLE mcp_readonly IS 'Read-only role for MCP (Model Context Protocol) database access. Used by AI/LLM tools like Claude Code, Claude Desktop, Cursor, etc.';

    -- ===============================================================
    -- Schema: mes_core - Read-Only Access
    -- ===============================================================

    GRANT CONNECT ON DATABASE "proveit-mes" TO mcp_readonly;
    GRANT USAGE ON SCHEMA mes_core TO mcp_readonly;

    -- Grant SELECT on all existing tables
    GRANT SELECT ON ALL TABLES IN SCHEMA mes_core TO mcp_readonly;

    -- Grant SELECT on all existing sequences (needed for reading serial values)
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA mes_core TO mcp_readonly;

    -- Grant EXECUTE on functions (for views that use functions)
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA mes_core TO mcp_readonly;

    -- Ensure future tables/sequences/functions also get SELECT
    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_core
    GRANT SELECT ON TABLES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_core
    GRANT SELECT ON SEQUENCES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_core
    GRANT EXECUTE ON FUNCTIONS TO mcp_readonly;

    -- ===============================================================
    -- Schema: mes_audit - Read-Only Access
    -- ===============================================================

    GRANT USAGE ON SCHEMA mes_audit TO mcp_readonly;

    -- Grant SELECT on all existing tables (audit logs are read-only anyway)
    GRANT SELECT ON ALL TABLES IN SCHEMA mes_audit TO mcp_readonly;
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA mes_audit TO mcp_readonly;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA mes_audit TO mcp_readonly;

    -- Ensure future tables/sequences/functions also get SELECT
    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_audit
    GRANT SELECT ON TABLES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_audit
    GRANT SELECT ON SEQUENCES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_audit
    GRANT EXECUTE ON FUNCTIONS TO mcp_readonly;

    -- ===============================================================
    -- Schema: mes_custom - Read-Only Access
    -- ===============================================================

    GRANT USAGE ON SCHEMA mes_custom TO mcp_readonly;

    -- Grant SELECT on all existing tables
    GRANT SELECT ON ALL TABLES IN SCHEMA mes_custom TO mcp_readonly;
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA mes_custom TO mcp_readonly;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA mes_custom TO mcp_readonly;

    -- Ensure future tables/sequences/functions also get SELECT
    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_custom
    GRANT SELECT ON TABLES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_custom
    GRANT SELECT ON SEQUENCES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA mes_custom
    GRANT EXECUTE ON FUNCTIONS TO mcp_readonly;

    -- ===============================================================
    -- Schema: public - Read-Only Access (for schema_version, etc.)
    -- ===============================================================

    GRANT USAGE ON SCHEMA public TO mcp_readonly;

    GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO mcp_readonly;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO mcp_readonly;

    ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO mcp_readonly;

    -- ===============================================================
    -- TimescaleDB Internal Access (Required for Hypertable Queries)
    -- ===============================================================

    -- Grant access to TimescaleDB internal schemas for querying hypertables
    GRANT USAGE ON SCHEMA _timescaledb_catalog TO mcp_readonly;
    GRANT USAGE ON SCHEMA _timescaledb_internal TO mcp_readonly;
    GRANT USAGE ON SCHEMA timescaledb_information TO mcp_readonly;

    GRANT SELECT ON ALL TABLES IN SCHEMA _timescaledb_catalog TO mcp_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA _timescaledb_internal TO mcp_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA timescaledb_information TO mcp_readonly;

EOSQL

echo "MCP read-only user created successfully."
