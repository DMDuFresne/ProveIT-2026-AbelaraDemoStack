/**
 * Schema introspection module
 * Queries PostgreSQL catalog to discover tables, columns, functions,
 * and database/schema-level comments for self-documentation
 */

import { rawQuery } from './client.js';
import { getConfig } from '../config.js';
import {
  TableInfo,
  ColumnInfo,
  FunctionInfo,
  FunctionParameter,
  SchemaMetadata,
  DatabaseContext,
} from '../types/index.js';

let cachedSchema: SchemaMetadata | null = null;
let cachedDatabaseContext: DatabaseContext | null = null;
let lastRefreshTime: number = 0;

/**
 * Load table and view information from the database
 */
async function loadTablesAndViews(): Promise<{ tables: TableInfo[]; views: TableInfo[] }> {
  const config = getConfig();
  const schemas = config.exposedSchemas;
  const schemaPlaceholders = schemas.map((_, i) => `$${i + 1}`).join(', ');

  // Query tables and views
  const tablesQuery = `
    SELECT
      t.table_schema,
      t.table_name,
      t.table_type,
      obj_description((t.table_schema || '.' || t.table_name)::regclass) as table_comment
    FROM information_schema.tables t
    WHERE t.table_schema IN (${schemaPlaceholders})
      AND t.table_type IN ('BASE TABLE', 'VIEW')
    ORDER BY t.table_schema, t.table_name
  `;

  const tablesResult = await rawQuery<{
    table_schema: string;
    table_name: string;
    table_type: string;
    table_comment: string | null;
  }>(tablesQuery, schemas);

  // Query columns for all tables
  const columnsQuery = `
    SELECT
      c.table_schema,
      c.table_name,
      c.column_name,
      c.data_type,
      c.is_nullable,
      c.column_default,
      c.ordinal_position,
      col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as column_comment,
      CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
      CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key,
      fk.foreign_table_schema || '.' || fk.foreign_table_name as fk_table,
      fk.foreign_column_name as fk_column
    FROM information_schema.columns c
    LEFT JOIN (
      SELECT
        n.nspname AS table_schema,
        cl.relname AS table_name,
        a.attname AS column_name
      FROM pg_constraint con
      JOIN pg_class cl ON con.conrelid = cl.oid
      JOIN pg_namespace n ON cl.relnamespace = n.oid
      JOIN pg_attribute a ON a.attrelid = con.conrelid
        AND a.attnum = ANY(con.conkey)
      WHERE con.contype = 'p'
    ) pk ON c.table_schema = pk.table_schema
        AND c.table_name = pk.table_name
        AND c.column_name = pk.column_name
    LEFT JOIN (
      SELECT
        n.nspname AS table_schema,
        cl.relname AS table_name,
        a.attname AS column_name,
        fn.nspname AS foreign_table_schema,
        fcl.relname AS foreign_table_name,
        fa.attname AS foreign_column_name
      FROM pg_constraint con
      JOIN pg_class cl ON con.conrelid = cl.oid
      JOIN pg_namespace n ON cl.relnamespace = n.oid
      JOIN pg_class fcl ON con.confrelid = fcl.oid
      JOIN pg_namespace fn ON fcl.relnamespace = fn.oid
      CROSS JOIN LATERAL unnest(con.conkey, con.confkey)
        WITH ORDINALITY AS cols(conkey_col, confkey_col, ord)
      JOIN pg_attribute a ON a.attrelid = con.conrelid
        AND a.attnum = cols.conkey_col
      JOIN pg_attribute fa ON fa.attrelid = con.confrelid
        AND fa.attnum = cols.confkey_col
      WHERE con.contype = 'f'
    ) fk ON c.table_schema = fk.table_schema
        AND c.table_name = fk.table_name
        AND c.column_name = fk.column_name
    WHERE c.table_schema IN (${schemaPlaceholders})
    ORDER BY c.table_schema, c.table_name, c.ordinal_position
  `;

  const columnsResult = await rawQuery<{
    table_schema: string;
    table_name: string;
    column_name: string;
    data_type: string;
    is_nullable: string;
    column_default: string | null;
    ordinal_position: number;
    column_comment: string | null;
    is_primary_key: boolean;
    is_foreign_key: boolean;
    fk_table: string | null;
    fk_column: string | null;
  }>(columnsQuery, schemas);

  // Build column map
  const columnMap = new Map<string, ColumnInfo[]>();
  for (const col of columnsResult.rows) {
    const key = `${col.table_schema}.${col.table_name}`;
    if (!columnMap.has(key)) {
      columnMap.set(key, []);
    }
    columnMap.get(key)!.push({
      columnName: col.column_name,
      dataType: col.data_type,
      isNullable: col.is_nullable === 'YES',
      columnDefault: col.column_default,
      isPrimaryKey: col.is_primary_key,
      isForeignKey: col.is_foreign_key,
      foreignKeyTable: col.fk_table,
      foreignKeyColumn: col.fk_column,
      comment: col.column_comment,
      ordinalPosition: col.ordinal_position,
    });
  }

  // Build table/view lists
  const tables: TableInfo[] = [];
  const views: TableInfo[] = [];

  for (const row of tablesResult.rows) {
    const key = `${row.table_schema}.${row.table_name}`;
    const info: TableInfo = {
      schemaName: row.table_schema,
      tableName: row.table_name,
      tableType: row.table_type === 'VIEW' ? 'view' : 'table',
      comment: row.table_comment,
      columns: columnMap.get(key) || [],
    };

    if (row.table_type === 'VIEW') {
      views.push(info);
    } else {
      tables.push(info);
    }
  }

  return { tables, views };
}

/**
 * Load function information from the database
 */
async function loadFunctions(): Promise<FunctionInfo[]> {
  const config = getConfig();
  const schemas = config.exposedSchemas;
  const schemaPlaceholders = schemas.map((_, i) => `$${i + 1}`).join(', ');

  // Note: prokind = 'f' filters for regular functions only
  // ('a' = aggregate, 'w' = window, 'p' = procedure, 'f' = function)
  // proisagg was removed in PostgreSQL 17, so we rely solely on prokind
  const functionsQuery = `
    SELECT
      n.nspname as schema_name,
      p.proname as function_name,
      pg_get_function_result(p.oid) as return_type,
      pg_get_function_arguments(p.oid) as arguments,
      d.description as function_comment,
      p.provolatile as volatility
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    LEFT JOIN pg_description d ON p.oid = d.objoid
    WHERE n.nspname IN (${schemaPlaceholders})
      AND p.prokind = 'f'
    ORDER BY n.nspname, p.proname
  `;

  const result = await rawQuery<{
    schema_name: string;
    function_name: string;
    return_type: string;
    arguments: string;
    function_comment: string | null;
    volatility: string;
  }>(functionsQuery, schemas);

  return result.rows.map(row => ({
    schemaName: row.schema_name,
    functionName: row.function_name,
    returnType: row.return_type,
    parameters: parseArguments(row.arguments),
    comment: row.function_comment,
    isVolatile: row.volatility === 'v',
  }));
}

/**
 * Parse PostgreSQL function arguments string into structured parameters
 */
function parseArguments(argsStr: string): FunctionParameter[] {
  if (!argsStr || argsStr.trim() === '') {
    return [];
  }

  const params: FunctionParameter[] = [];
  const args = argsStr.split(',').map(a => a.trim());

  for (const arg of args) {
    const parts = arg.split(/\s+/);
    let mode: FunctionParameter['mode'] = 'IN';
    let name = '';
    let dataType = '';
    let defaultValue: string | null = null;

    // Check for mode prefix
    if (parts[0] === 'IN' || parts[0] === 'OUT' || parts[0] === 'INOUT' || parts[0] === 'VARIADIC') {
      mode = parts[0] as FunctionParameter['mode'];
      parts.shift();
    }

    // Check for DEFAULT
    const defaultIdx = parts.findIndex(p => p.toUpperCase() === 'DEFAULT');
    if (defaultIdx !== -1) {
      defaultValue = parts.slice(defaultIdx + 1).join(' ');
      parts.splice(defaultIdx);
    }

    // Remaining parts: name and type
    if (parts.length >= 2) {
      name = parts[0];
      dataType = parts.slice(1).join(' ');
    } else if (parts.length === 1) {
      dataType = parts[0];
    }

    params.push({ name, dataType, mode, defaultValue });
  }

  return params;
}

/**
 * Load complete schema metadata
 */
export async function loadSchemaMetadata(): Promise<SchemaMetadata> {
  const { tables, views } = await loadTablesAndViews();
  const functions = await loadFunctions();

  return {
    tables,
    views,
    functions,
    lastRefreshed: new Date(),
  };
}

/**
 * Get schema metadata with caching
 */
export async function getSchemaMetadata(forceRefresh = false): Promise<SchemaMetadata> {
  const config = getConfig();
  const now = Date.now();

  if (
    forceRefresh ||
    !cachedSchema ||
    now - lastRefreshTime > config.schemaRefreshIntervalMs
  ) {
    cachedSchema = await loadSchemaMetadata();
    lastRefreshTime = now;
  }

  return cachedSchema;
}

/**
 * Get a specific table by schema and name
 */
export async function getTable(
  schemaName: string,
  tableName: string
): Promise<TableInfo | null> {
  const schema = await getSchemaMetadata();
  const allTables = [...schema.tables, ...schema.views];

  return (
    allTables.find(
      t =>
        t.schemaName.toLowerCase() === schemaName.toLowerCase() &&
        t.tableName.toLowerCase() === tableName.toLowerCase()
    ) || null
  );
}

/**
 * Clear the schema cache
 */
export function clearSchemaCache(): void {
  cachedSchema = null;
  cachedDatabaseContext = null;
  lastRefreshTime = 0;
}

/**
 * Load database-level and schema-level comments for self-documentation
 */
async function loadDatabaseContext(): Promise<DatabaseContext> {
  const config = getConfig();
  const schemas = config.exposedSchemas;
  const schemaPlaceholders = schemas.map((_, i) => `$${i + 1}`).join(', ');

  // Query database-level comment
  const dbCommentQuery = `
    SELECT
      current_database() as db_name,
      pg_catalog.shobj_description(oid, 'pg_database') as db_comment
    FROM pg_database
    WHERE datname = current_database()
  `;

  const dbResult = await rawQuery<{
    db_name: string;
    db_comment: string | null;
  }>(dbCommentQuery, []);

  // Query schema-level comments
  const schemaCommentQuery = `
    SELECT
      nspname as schema_name,
      obj_description(oid, 'pg_namespace') as schema_comment
    FROM pg_namespace
    WHERE nspname IN (${schemaPlaceholders})
  `;

  const schemaResult = await rawQuery<{
    schema_name: string;
    schema_comment: string | null;
  }>(schemaCommentQuery, schemas);

  // Build schema comments map
  const schemaComments: Record<string, string> = {};
  for (const row of schemaResult.rows) {
    if (row.schema_comment) {
      schemaComments[row.schema_name] = row.schema_comment;
    }
  }

  return {
    databaseName: dbResult.rows[0]?.db_name || 'unknown',
    databaseComment: dbResult.rows[0]?.db_comment || null,
    schemaComments,
  };
}

/**
 * Get database context with caching
 */
export async function getDatabaseContext(forceRefresh = false): Promise<DatabaseContext> {
  const config = getConfig();
  const now = Date.now();

  if (
    forceRefresh ||
    !cachedDatabaseContext ||
    now - lastRefreshTime > config.schemaRefreshIntervalMs
  ) {
    cachedDatabaseContext = await loadDatabaseContext();
  }

  return cachedDatabaseContext;
}

/**
 * Force refresh of all cached metadata
 * Returns a summary of what was loaded
 */
export async function forceRefreshSchema(): Promise<{
  tables: number;
  views: number;
  functions: number;
  schemasWithComments: number;
  hasDatabaseComment: boolean;
}> {
  clearSchemaCache();

  const [schema, context] = await Promise.all([
    getSchemaMetadata(true),
    getDatabaseContext(true),
  ]);

  return {
    tables: schema.tables.length,
    views: schema.views.length,
    functions: schema.functions.length,
    schemasWithComments: Object.keys(context.schemaComments).length,
    hasDatabaseComment: !!context.databaseComment,
  };
}
