/**
 * Describe Table tool - Get detailed table/view information
 */

import { z } from 'zod';
import { generateTableDescription } from '../descriptions/generator.js';
import { getDescribeTableToolDescription } from '../descriptions/generator.js';

export const describeTableToolName = 'describe_table';

export const describeTableToolSchema = z.object({
  schema: z
    .string()
    .default('mes_core')
    .describe('Schema name (default: mes_core)'),
  table: z.string().min(1).describe('Table or view name'),
});

export type DescribeTableToolInput = z.infer<typeof describeTableToolSchema>;

export function getDescribeTableToolDefinition() {
  return {
    name: describeTableToolName,
    description: getDescribeTableToolDescription(),
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

export async function executeDescribeTableTool(
  input: DescribeTableToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const schemaName = input.schema || 'mes_core';
    const description = await generateTableDescription(schemaName, input.table);

    return {
      content: [{ type: 'text', text: description }],
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      content: [
        {
          type: 'text',
          text: `Error describing table: ${errorMessage}`,
        },
      ],
    };
  }
}
