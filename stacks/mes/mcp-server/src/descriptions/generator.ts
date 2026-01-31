/**
 * Description generator module
 * Combines static descriptions with dynamic schema data
 */

import { getSchemaMetadata, getTable } from '../database/schema-loader.js';
import { TableInfo, FunctionInfo, SchemaMetadata } from '../types/index.js';
import {
  TABLE_DESCRIPTIONS,
  FUNCTION_DESCRIPTIONS,
  QUERY_TOOL_DESCRIPTION,
  MES_CONCEPTS,
  SCHEMA_OVERVIEW,
} from './static.js';

/**
 * Get enhanced description for a table, combining database comment with static description
 */
export function getTableDescription(table: TableInfo): string {
  const key = `${table.schemaName}.${table.tableName}`;
  const staticDesc = TABLE_DESCRIPTIONS[key];
  const dbComment = table.comment;

  if (staticDesc && dbComment) {
    return `${staticDesc}\n\nDatabase comment: ${dbComment}`;
  }

  return staticDesc || dbComment || 'No description available.';
}

/**
 * Get enhanced description for a function
 */
export function getFunctionDescription(func: FunctionInfo): string {
  const key = `${func.schemaName}.${func.functionName}`;
  const staticDesc = FUNCTION_DESCRIPTIONS[key];
  const dbComment = func.comment;

  if (staticDesc && dbComment) {
    return `${staticDesc}\n\nDatabase comment: ${dbComment}`;
  }

  return staticDesc || dbComment || 'No description available.';
}

/**
 * Format column information for display
 */
export function formatColumnInfo(table: TableInfo): string {
  const lines: string[] = [];

  for (const col of table.columns) {
    let line = `  - ${col.columnName}: ${col.dataType}`;

    const modifiers: string[] = [];
    if (col.isPrimaryKey) modifiers.push('PK');
    if (col.isForeignKey) {
      modifiers.push(`FK → ${col.foreignKeyTable}.${col.foreignKeyColumn}`);
    }
    if (!col.isNullable) modifiers.push('NOT NULL');
    if (col.columnDefault) modifiers.push(`DEFAULT: ${col.columnDefault}`);

    if (modifiers.length > 0) {
      line += ` [${modifiers.join(', ')}]`;
    }

    if (col.comment) {
      line += `\n    "${col.comment}"`;
    }

    lines.push(line);
  }

  return lines.join('\n');
}

/**
 * Generate table list description
 */
export async function generateTableListDescription(
  schemaFilter?: string
): Promise<string> {
  const schema = await getSchemaMetadata();
  let tables = [...schema.tables, ...schema.views];

  if (schemaFilter) {
    tables = tables.filter(
      t => t.schemaName.toLowerCase() === schemaFilter.toLowerCase()
    );
  }

  const grouped = new Map<string, TableInfo[]>();
  for (const table of tables) {
    if (!grouped.has(table.schemaName)) {
      grouped.set(table.schemaName, []);
    }
    grouped.get(table.schemaName)!.push(table);
  }

  const lines: string[] = [];

  for (const [schemaName, schemaTables] of grouped) {
    lines.push(`\n## Schema: ${schemaName}`);
    lines.push('');

    const tableList = schemaTables.filter(t => t.tableType === 'table');
    const viewList = schemaTables.filter(t => t.tableType === 'view');

    if (tableList.length > 0) {
      lines.push('### Tables');
      for (const table of tableList) {
        const desc = getTableDescription(table);
        lines.push(`- **${table.tableName}**: ${desc.split('\n')[0]}`);
      }
      lines.push('');
    }

    if (viewList.length > 0) {
      lines.push('### Views');
      for (const view of viewList) {
        const desc = getTableDescription(view);
        lines.push(`- **${view.tableName}**: ${desc.split('\n')[0]}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}

/**
 * Generate detailed table description
 */
export async function generateTableDescription(
  schemaName: string,
  tableName: string
): Promise<string> {
  const table = await getTable(schemaName, tableName);

  if (!table) {
    return `Table ${schemaName}.${tableName} not found.`;
  }

  const lines: string[] = [];

  lines.push(`# ${table.schemaName}.${table.tableName}`);
  lines.push(`Type: ${table.tableType.toUpperCase()}`);
  lines.push('');
  lines.push('## Description');
  lines.push(getTableDescription(table));
  lines.push('');
  lines.push('## Columns');
  lines.push(formatColumnInfo(table));

  return lines.join('\n');
}

/**
 * Generate complete schema overview as JSON
 */
export async function generateSchemaOverview(): Promise<SchemaMetadata> {
  return await getSchemaMetadata();
}

/**
 * Generate the complete query tool description
 */
export function getQueryToolDescription(): string {
  return QUERY_TOOL_DESCRIPTION;
}

/**
 * Generate list_tables tool description
 */
export function getListTablesToolDescription(): string {
  return `List all tables and views in the MES database.

${MES_CONCEPTS}

Optionally filter by schema name. Returns table names with descriptions.`;
}

/**
 * Generate describe_table tool description
 */
export function getDescribeTableToolDescription(): string {
  return `Get detailed information about a specific table or view.

Returns column names, data types, constraints, foreign keys, and descriptions.

${SCHEMA_OVERVIEW}`;
}

/**
 * Generate schema_overview tool description
 */
export function getSchemaOverviewToolDescription(): string {
  return `Get complete schema metadata as structured JSON.

Returns all tables, views, functions with their columns, parameters, and descriptions.

Useful for understanding the database structure programmatically.

${MES_CONCEPTS}`;
}
