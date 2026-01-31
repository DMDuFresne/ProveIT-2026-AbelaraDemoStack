/**
 * List Tables tool - List all tables and views with descriptions
 */

import { z } from 'zod';
import { generateTableListDescription } from '../descriptions/generator.js';
import { getListTablesToolDescription } from '../descriptions/generator.js';

export const listTablesToolName = 'list_tables';

export const listTablesToolSchema = z.object({
  schema: z
    .string()
    .optional()
    .describe(
      'Optional schema name to filter (e.g., "mes_core", "mes_audit", "mes_custom")'
    ),
});

export type ListTablesToolInput = z.infer<typeof listTablesToolSchema>;

export function getListTablesToolDefinition() {
  return {
    name: listTablesToolName,
    description: getListTablesToolDescription(),
    inputSchema: {
      type: 'object' as const,
      properties: {
        schema: {
          type: 'string',
          description:
            'Optional schema name to filter (e.g., "mes_core", "mes_audit", "mes_custom")',
        },
      },
      required: [],
    },
  };
}

export async function executeListTablesTool(
  input: ListTablesToolInput
): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
  try {
    const description = await generateTableListDescription(input.schema);

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
          text: `Error listing tables: ${errorMessage}`,
        },
      ],
    };
  }
}
