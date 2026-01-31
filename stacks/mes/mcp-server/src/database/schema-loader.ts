/**
 * Schema introspection module
 * Queries PostgreSQL catalog to discover tables, columns, and functions
 */

import { rawQuery } from './client.js';
import { getConfig } from '../config.js';
import {
  TableInfo,
  ColumnInfo,
  FunctionInfo,
  FunctionParameter,
  SchemaMetadata,
} from '../types/index.js';

let cachedSchema: SchemaMetadata | null = null;
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
        kcu.table_schema,
        kcu.table_name,
        kcu.column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      WHERE tc.constraint_type = 'PRIMARY KEY'
    ) pk ON c.table_schema = pk.table_schema
        AND c.table_name = pk.table_name
        AND c.column_name = pk.column_name
    LEFT JOIN (
      SELECT
        kcu.table_schema,
        kcu.table_name,
        kcu.column_name,
        ccu.table_schema as foreign_table_schema,
        ccu.table_name as foreign_table_name,
        ccu.column_name as foreign_column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      JOIN information_schema.constraint_column_usage ccu
        ON tc.constraint_name = ccu.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY'
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
  lastRefreshTime = 0;
}
