/**
 * Get Sample Data tool - Return sample rows from a table
 */

import { z } from 'zod';
import { query } from '../database/client.js';
import { getTable } from '../database/schema-loader.js';

export const getSampleDataToolName = 'get_sample_data';

export const getSampleDataToolSchema = z.object({
  schema: z
    .string()
    .default('mes_core')
    .describe('Schema name (default: mes_core)'),
  table: z.string().min(1).describe('Table or view name'),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .default(5)
    .describe('Number of rows to return (1-20, default: 5)'),
});

export type GetSampleDataToolInput = z.infer<typeof getSampleDataToolSchema>;

export function getGetSampleDataToolDefinition() {
  return {
    name: getSampleDataToolName,
    description: `Get sample rows from a table or view to understand actual data patterns.

Returns a small set of rows (default 5, max 20) to help understand:
- Actual data formats and values
- Column content patterns
- Typical record structures

For time-series tables (logs), returns most recent rows.
For master data tables, returns a random sample.`,
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
        limit: {
          type: 'number',
          description: 'Number of rows to return (1-20, default: 5)',
          default: 5,
        },
      },
      required: ['table'],
    },
  };
}

export async function executeGetSampleDataTool(
  input: GetSampleDataToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const schemaName = input.schema || 'mes_core';
    const limit = input.limit || 5;

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

    // Determine ordering - use logged_at for log tables, otherwise random
    const hasLoggedAt = tableInfo.columns.some(c => c.columnName === 'logged_at');
    const hasCreatedAt = tableInfo.columns.some(c => c.columnName === 'created_at');

    let orderClause: string;
    if (hasLoggedAt) {
      orderClause = 'ORDER BY logged_at DESC';
    } else if (hasCreatedAt) {
      orderClause = 'ORDER BY created_at DESC';
    } else {
      orderClause = 'ORDER BY RANDOM()';
    }

    // Build and execute query
    const sql = `SELECT * FROM ${schemaName}.${input.table} ${orderClause} LIMIT ${limit}`;
    const result = await query(sql);

    const output = {
      table: `${schemaName}.${input.table}`,
      sampleSize: result.rowCount,
      columns: result.columns,
      rows: result.rows,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(output, null, 2),
        },
      ],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error getting sample data: ${errorMessage}`,
        },
      ],
    };
  }
}
