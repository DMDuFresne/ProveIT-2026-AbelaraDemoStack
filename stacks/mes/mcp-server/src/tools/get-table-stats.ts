/**
 * Get Table Stats tool - Row counts, null percentages, distinct values
 */

import { z } from 'zod';
import { query, rawQuery } from '../database/client.js';
import { getTable } from '../database/schema-loader.js';

export const getTableStatsToolName = 'get_table_stats';

export const getTableStatsToolSchema = z.object({
  schema: z
    .string()
    .default('mes_core')
    .describe('Schema name (default: mes_core)'),
  table: z.string().min(1).describe('Table or view name'),
});

export type GetTableStatsToolInput = z.infer<typeof getTableStatsToolSchema>;

export function getGetTableStatsToolDefinition() {
  return {
    name: getTableStatsToolName,
    description: `Get statistics about a table including row count and column statistics.

Returns:
- Total row count
- For each column: null count, null percentage, distinct value count

Useful for understanding:
- Data distribution and quality
- Column cardinality for query optimization
- Identifying sparse columns

Note: Statistics are calculated on current data and may take time for large tables.`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        schema: {
          type: 'string',
          description: 'Schema name (default: mes_core)',
          default: 'mes_core',
        },
        table: {
          type: 'string',
          description: 'Table or view name',
        },
      },
      required: ['table'],
    },
  };
}

export async function executeGetTableStatsTool(
  input: GetTableStatsToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const schemaName = input.schema || 'mes_core';

    // Verify table exists
    const tableInfo = await getTable(schemaName, input.table);
    if (!tableInfo) {
      return {
        content: [
          {
            type: 'text',
            text: `Table ${schemaName}.${input.table} not found.`,
          },
        ],
      };
    }

    // Get row count
    const countResult = await query(
      `SELECT COUNT(*) as total FROM ${schemaName}.${input.table}`
    );
    const totalRows = parseInt(countResult.rows[0]?.total as string, 10) || 0;

    if (totalRows === 0) {
      return {
        content: [
          {
            type: 'text',
            text: `Table ${schemaName}.${input.table} is empty (0 rows).`,
          },
        ],
      };
    }

    // Build column statistics query
    // For each column: count nulls and distinct values
    const columnStats: Array<{
      column: string;
      dataType: string;
      nullCount: number;
      nullPercent: number;
      distinctCount: number;
    }> = [];

    // Process columns in batches to avoid overly complex queries
    for (const col of tableInfo.columns) {
      try {
        const statsQuery = `
          SELECT
            COUNT(*) - COUNT(${quoteIdentifier(col.columnName)}) as null_count,
            COUNT(DISTINCT ${quoteIdentifier(col.columnName)}) as distinct_count
          FROM ${schemaName}.${input.table}
        `;

        const statsResult = await rawQuery<{
          null_count: string;
          distinct_count: string;
        }>(statsQuery);

        const nullCount = parseInt(statsResult.rows[0]?.null_count || '0', 10);
        const distinctCount = parseInt(statsResult.rows[0]?.distinct_count || '0', 10);

        columnStats.push({
          column: col.columnName,
          dataType: col.dataType,
          nullCount,
          nullPercent: Math.round((nullCount / totalRows) * 100 * 10) / 10,
          distinctCount,
        });
      } catch {
        // Some columns may not support COUNT DISTINCT (e.g., jsonb)
        columnStats.push({
          column: col.columnName,
          dataType: col.dataType,
          nullCount: -1,
          nullPercent: -1,
          distinctCount: -1,
        });
      }
    }

    // Format output
    const lines: string[] = [];
    lines.push(`## Statistics for ${schemaName}.${input.table}\n`);
    lines.push(`**Total Rows:** ${totalRows.toLocaleString()}\n`);
    lines.push('### Column Statistics\n');
    lines.push('| Column | Type | Nulls | Null % | Distinct |');
    lines.push('|--------|------|-------|--------|----------|');

    for (const stat of columnStats) {
      const nullStr = stat.nullCount >= 0 ? stat.nullCount.toLocaleString() : 'N/A';
      const nullPctStr = stat.nullPercent >= 0 ? `${stat.nullPercent}%` : 'N/A';
      const distinctStr = stat.distinctCount >= 0 ? stat.distinctCount.toLocaleString() : 'N/A';

      lines.push(
        `| ${stat.column} | ${stat.dataType} | ${nullStr} | ${nullPctStr} | ${distinctStr} |`
      );
    }

    return {
      content: [{ type: 'text', text: lines.join('\n') }],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error getting table stats: ${errorMessage}`,
        },
      ],
    };
  }
}

function quoteIdentifier(name: string): string {
  return `"${name.replace(/"/g, '""')}"`;
}
