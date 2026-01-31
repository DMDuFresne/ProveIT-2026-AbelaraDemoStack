/**
 * Type definitions for the MES MCP Server
 */

/**
 * Column information from database introspection
 */
export interface ColumnInfo {
  columnName: string;
  dataType: string;
  isNullable: boolean;
  columnDefault: string | null;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  foreignKeyTable: string | null;
  foreignKeyColumn: string | null;
  comment: string | null;
  ordinalPosition: number;
}

/**
 * Table or view information from database introspection
 */
export interface TableInfo {
  schemaName: string;
  tableName: string;
  tableType: 'table' | 'view';
  comment: string | null;
  columns: ColumnInfo[];
  rowCount?: number;
}

/**
 * Function parameter information
 */
export interface FunctionParameter {
  name: string;
  dataType: string;
  mode: 'IN' | 'OUT' | 'INOUT' | 'VARIADIC';
  defaultValue: string | null;
}

/**
 * Function information from database introspection
 */
export interface FunctionInfo {
  schemaName: string;
  functionName: string;
  returnType: string;
  parameters: FunctionParameter[];
  comment: string | null;
  isVolatile: boolean;
}

/**
 * Complete schema metadata
 */
export interface SchemaMetadata {
  tables: TableInfo[];
  views: TableInfo[];
  functions: FunctionInfo[];
  lastRefreshed: Date;
}

/**
 * Query result with metadata
 */
export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  truncated: boolean;
}

/**
 * Tool execution result
 */
export interface ToolResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

/**
 * Dangerous SQL keywords that should be blocked
 */
export const BLOCKED_KEYWORDS = [
  'INSERT',
  'UPDATE',
  'DELETE',
  'DROP',
  'CREATE',
  'ALTER',
  'TRUNCATE',
  'GRANT',
  'REVOKE',
  'COMMIT',
  'ROLLBACK',
  'SAVEPOINT',
  'COPY',
  'VACUUM',
  'ANALYZE',
  'REINDEX',
  'CLUSTER',
  'REFRESH',
  'LOCK',
  'UNLISTEN',
  'LISTEN',
  'NOTIFY',
  'RESET',
  'SET',
  'DISCARD',
  'PREPARE',
  'EXECUTE',
  'DEALLOCATE',
  'DECLARE',
  'FETCH',
  'MOVE',
  'CLOSE',
  'CALL',
] as const;

export type BlockedKeyword = typeof BLOCKED_KEYWORDS[number];
