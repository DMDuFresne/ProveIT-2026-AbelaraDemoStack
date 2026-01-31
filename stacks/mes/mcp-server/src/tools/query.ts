/**
 * Query tool - Execute read-only SQL queries
 */

import { z } from 'zod';
import { query as executeQuery } from '../database/client.js';
import { getQueryToolDescription } from '../descriptions/generator.js';

export const queryToolName = 'query';

export const queryToolSchema = z.object({
  sql: z
    .string()
    .min(1)
    .describe('The SQL SELECT query to execute'),
});

export type QueryToolInput = z.infer<typeof queryToolSchema>;

export function getQueryToolDefinition() {
  return {
    name: queryToolName,
    description: getQueryToolDescription(),
    inputSchema: {
      type: 'object' as const,
      properties: {
        sql: {
          type: 'string',
          description: 'The SQL SELECT query to execute',
        },
      },
      required: ['sql'],
    },
  };
}

export async function executeQueryTool(
  input: QueryToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const result = await executeQuery(input.sql);

    const output = {
      success: true,
      columns: result.columns,
      rows: result.rows,
      rowCount: result.rowCount,
      truncated: result.truncated,
    };

    let text = JSON.stringify(output, null, 2);

    if (result.truncated) {
      text += `\n\n⚠️ Results truncated. Query returned ${result.rowCount} rows but only showing first rows. Add LIMIT to your query for better control.`;
    }

    return {
      content: [{ type: 'text', text }],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              success: false,
              error: errorMessage,
            },
            null,
            2
          ),
        },
      ],
    };
  }
}
